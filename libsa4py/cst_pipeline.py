import os
import traceback
import random
import csv
import time

from typing import List, Dict
from os.path import join
from pathlib import Path
from datetime import timedelta
from joblib import delayed
from dpu_utils.utils.dataloading import load_jsonl_gz
from libsa4py.cst_extractor import Extractor
from libsa4py.cst_transformers import TypeApplier
from libsa4py.exceptions import ParseError, NullProjectException
from libsa4py.nl_preprocessing import NLPreprocessor
from libsa4py.utils import read_file, list_files, ParallelExecutor, mk_dir_not_exist, save_json, load_json, write_file
from libsa4py.pyre import pyre_server_init, pyre_query_types, pyre_server_shutdown, pyre_kill_all_servers, \
    clean_pyre_config
from libsa4py.type_check import MypyManager, type_check_single_file
from libsa4py import MAX_TC_TIME

import libcst as cst
import logging
import logging.config


class Pipeline:
    """
    This is the new pipeline that converts a project to the output JSON of LibCST analysis
    """

    def __init__(self, projects_path, output_dir, nlp_transf: bool = True,
                 use_cache: bool = True, use_pyre: bool = False, use_tc: bool = False,
                 dups_files_path=None, split_files_path=None):
        self.projects_path = projects_path
        self.output_dir = output_dir
        self.processed_projects = None
        self.err_log_dir = None
        self.avl_types_dir = None
        self.nlp_transf = nlp_transf
        self.use_cache = use_cache
        self.use_pyre = use_pyre
        self.use_tc = use_tc
        self.nlp_prep = NLPreprocessor()

        self.__make_output_dirs()

        if dups_files_path is not None:
            clusters_rand_files = [l.pop(random.randrange(len(l))) for l in load_jsonl_gz(dups_files_path)]
            self.duplicate_files = [f for l in load_jsonl_gz(dups_files_path) for f in l]
            self.duplicate_files = set(self.duplicate_files).difference(set(clusters_rand_files))
            self.is_file_duplicate = lambda x: True if x in self.duplicate_files else False
        else:
            self.is_file_duplicate = lambda x: False

        if self.use_tc:
            self.tc = MypyManager('mypy', MAX_TC_TIME)

        self.split_dataset_files = {f:s for s, f in csv.reader(open(split_files_path, 'r'))} if split_files_path is not None else {}

        # TODO: Fix the logger issue not outputing the logs into the file.
        # logging.basicConfig(filename=join(self.err_log_dir, "pipeline_errors.log"), level=logging.DEBUG,
        #                     format='%(asctime)s %(name)s %(message)s')
        # self.logger = logging.getLogger(__name__)
        self.logger = self.__setup_pipeline_logger(join(self.err_log_dir, "pipeline_errors.log"))

    def __make_output_dirs(self):
        mk_dir_not_exist(self.output_dir)

        self.processed_projects = join(self.output_dir, "processed_projects")
        self.avl_types_dir = join(self.output_dir, "extracted_visible_types")
        self.err_log_dir = join(self.output_dir, "error_logs")
        mk_dir_not_exist(self.processed_projects)
        mk_dir_not_exist(self.avl_types_dir)
        mk_dir_not_exist(self.err_log_dir)

    def __setup_pipeline_logger(self, log_dir: str):
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)

        logger_ch = logging.StreamHandler()
        logger_ch.setLevel(logging.DEBUG)
    
        logger_fh = logging.FileHandler(filename=log_dir)
        logger_fh.setLevel(logging.DEBUG)
    
        logger_formatter = logging.Formatter(fmt='%(asctime)s - %(name)s - %(message)s')
        logger_ch.setFormatter(logger_formatter)
        logger_fh.setFormatter(logger_formatter)

        logger.addHandler(logger_ch)
        logger.addHandler(logger_fh)
    
        return logger

    def get_project_filename(self, project) -> str:
        """
        Return the filename at which a project datafile should be stored.
        :param project: the project dict
        :return: return filename
        """
        return join(self.processed_projects, f"{project['author']}{project['repo']}.json")

    def apply_nlp_transf(self, extracted_module: dict):
        """
        Applies NLP transformation to identifiers in a module
        """

        def fn_nlp_transf(fn_d: dict, nlp_prep: NLPreprocessor):
            fn_d['name'] = nlp_prep.process_identifier(fn_d['name'])
            fn_d['params'] = {nlp_prep.process_identifier(p): t for p, t in fn_d['params'].items()}
            fn_d['ret_exprs'] = [nlp_prep.process_identifier(r.replace('return ', '')) for r in fn_d['ret_exprs']]
            fn_d['params_occur'] = {p: [nlp_prep.process_sentence(j) for i in o for j in i] for p, o in
                                    fn_d['params_occur'].items()}
            fn_d['variables'] = {nlp_prep.process_identifier(v): t for v, t in fn_d['variables'].items()}
            fn_d['fn_var_occur'] = {v: [nlp_prep.process_sentence(j) for i in o for j in i] for v, o in
                                    fn_d['fn_var_occur'].items()}
            fn_d['params_descr'] = {nlp_prep.process_identifier(p): nlp_prep.process_sentence(fn_d['params_descr'][p]) \
                                    for p in fn_d['params_descr'].keys()}
            fn_d['docstring']['func'] = nlp_prep.process_sentence(fn_d['docstring']['func'])
            fn_d['docstring']['ret'] = nlp_prep.process_sentence(fn_d['docstring']['ret'])
            fn_d['docstring']['long_descr'] = nlp_prep.process_sentence(fn_d['docstring']['long_descr'])
            return fn_d

        extracted_module['variables'] = {self.nlp_prep.process_identifier(v): t for v, t in extracted_module['variables'].items()}
        extracted_module['mod_var_occur'] = {v: [self.nlp_prep.process_sentence(j) for i in o for j in i] for v,
                                             o in extracted_module['mod_var_occur'].items()}

        for c in extracted_module['classes']:
            c['variables'] = {self.nlp_prep.process_identifier(v): t for v, t in c['variables'].items()}
            c['cls_var_occur'] = {v: [self.nlp_prep.process_sentence(j) for i in o for j in i] for v,
                                  o in c['cls_var_occur'].items()}
            c['funcs'] = [fn_nlp_transf(f, self.nlp_prep) for f in c['funcs']]

        extracted_module['funcs'] = [fn_nlp_transf(f, self.nlp_prep) for f in extracted_module['funcs']]

        return extracted_module

    def process_project(self, i, project):

        project_id = f'{project["author"]}/{project["repo"]}'
        project_analyzed_files: dict = {project_id: {"src_files": {}, "type_annot_cove": 0.0}}
        try:
            print(f'Running pipeline for project {i} {project_id}')
            project['files'] = []

            print(f'Extracting for {project_id}...')
            extracted_avl_types = None

            project_files = list_files(join(self.projects_path, project["author"], project["repo"]))
            print(f"{project_id} has {len(project_files)} files before deduplication")
            project_files = [f for f in project_files if not self.is_file_duplicate(f)]
            print(f"{project_id} has {len(project_files)} files after deduplication")

            project_files = [(f, str(Path(f).relative_to(Path(self.projects_path).parent))) for f in project_files]
            project_files = [(f, f_r, self.split_dataset_files[f_r] if f_r in self.split_dataset_files else None) for f,
                             f_r in project_files]

            if len(project_files) != 0:
                if self.use_pyre:
                    print(f"Running pyre for {project_id}")
                    clean_pyre_config(join(self.projects_path, project["author"], project["repo"]))
                    pyre_server_init(join(self.projects_path, project["author"], project["repo"]))

                for filename, f_relative, f_split in project_files:
                    try:
                        pyre_data_file = pyre_query_types(join(self.projects_path, project["author"], project["repo"]),
                                                          filename) if self.use_pyre else None

                        project_analyzed_files[project_id]["src_files"][f_relative] = \
                            self.apply_nlp_transf(
                                Extractor().extract(read_file(filename), pyre_data_file).to_dict()) if self.nlp_transf \
                                else Extractor.extract(read_file(filename), pyre_data_file).to_dict()

                        project_analyzed_files[project_id]["src_files"][f_relative]['set'] = f_split
                        if self.use_tc:
                            print(f"Running type checker for file: {filename}")
                            project_analyzed_files[project_id]["src_files"][f_relative]['tc'] = \
                                type_check_single_file(filename, self.tc)

                        extracted_avl_types = project_analyzed_files[project_id]["src_files"][f_relative]['imports'] + \
                                              [c['name'] for c in
                                               project_analyzed_files[project_id]["src_files"][f_relative]['classes']]
                    except ParseError as err:
                        # print(f"Could not parse file {filename}")
                        traceback.print_exc()
                        self.logger.error("project: %s |file: %s |Exception: %s" % (project_id, filename, err))
                    except UnicodeDecodeError:
                        print(f"Could not read file {filename}")
                    except Exception as err:
                        # Other unexpected exceptions; Failure of single file should not
                        # fail the entire project processing.
                        # TODO: A better workaround would be to have a specialized exception thrown
                        # by the extractor, so that this exception is specialized.
                        #print(f"Could not process file {filename}")
                        traceback.print_exc()
                        self.logger.error("project: %s |file: %s |Exception: %s" % (project_id, filename, err))
                        #logging.error("project: %s |file: %s |Exception: %s" % (project_id, filename, err))

                print(f'Saving available type hints for {project_id}...')
                if self.avl_types_dir is not None:
                    if extracted_avl_types:
                        with open(join(self.avl_types_dir, f'{project["author"]}_{project["repo"]}_avltypes.txt'),
                                  'w') as f:
                            for t in extracted_avl_types:
                                f.write("%s\n" % t)

                if len(project_analyzed_files[project_id]["src_files"].keys()) != 0:
                    project_analyzed_files[project_id]["type_annot_cove"] = \
                        round(sum([project_analyzed_files[project_id]["src_files"][s]["type_annot_cove"] for s in
                                   project_analyzed_files[project_id]["src_files"].keys()]) / len(
                            project_analyzed_files[project_id]["src_files"].keys()), 2)

                    save_json(self.get_project_filename(project), project_analyzed_files)

                if self.use_pyre:
                    pyre_server_shutdown(join(self.projects_path, project["author"], project["repo"]))

            else:
                raise NullProjectException(project_id)

        except KeyboardInterrupt:
            quit(1)
        except NullProjectException as err:
            self.logger.error(err)
            print(err)
        except Exception as err:
            print(f'Running pipeline for project {i} failed')
            traceback.print_exc()
            self.logger.error("project: %s | Exception: %s" % (project_id, err))

    def run(self, repos_list: List[Dict], jobs, start=0):

        print(f"Number of projects to be processed: {len(repos_list)}")
        repos_list = [p for p in repos_list if not (os.path.exists(self.get_project_filename(p)) and self.use_cache)]
        print(f"Number of projects to be processed after considering cache: {len(repos_list)}")

        start_t = time.time()
        ParallelExecutor(n_jobs=jobs)(total=len(repos_list))(
            delayed(self.process_project)(i, project) for i, project in enumerate(repos_list, start=start))
        print("Finished processing %d projects in %s " % (len(repos_list), str(timedelta(seconds=time.time()-start_t))))

        if self.use_pyre:
            pyre_kill_all_servers()
        logging.shutdown()


class TypeAnnotatingProjects:
    """
    It applies the inferred type annotations to the input dataset
    """

    def __init__(self, projects_path: str, output_path: str, apply_nlp: bool = True):
        self.projects_path = projects_path
        self.output_path = output_path
        self.apply_nlp = apply_nlp

    def process_project(self, proj_json_path: str):
        proj_json = load_json(proj_json_path)
        for p in proj_json.keys():
            for i, (f, f_d) in enumerate(proj_json[p]['src_files'].items()):
                f_read = read_file(join(self.projects_path, f))
                if len(f_read) != 0:
                    try:
                        f_parsed = cst.parse_module(f_read)
                        try:
                            f_parsed = cst.metadata.MetadataWrapper(f_parsed).visit(TypeApplier(f_d, self.apply_nlp))
                            write_file(join(self.projects_path, f), f_parsed.code)
                        except KeyError as ke:
                            print(f"A variable not found | project {proj_json_path} | file {f}", ke)
                            traceback.print_exc()
                        except TypeError as te:
                            print(f"Project {proj_json_path} | file {f}", te)
                            traceback.print_exc()
                    except cst._exceptions.ParserSyntaxError as pse:
                        print(f"Can't parsed file {f} in project {proj_json_path}", pse)

    def run(self, jobs: int):
        proj_jsons = list_files(join(self.output_path, 'processed_projects'), '.json')
        proj_jsons.sort(key=lambda f: os.stat(f).st_size, reverse=True)
        ParallelExecutor(n_jobs=jobs)(total=len(proj_jsons))(delayed(self.process_project)(p_j) for p_j in proj_jsons)
