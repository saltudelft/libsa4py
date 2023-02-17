from libsa4py.cst_visitor import TypeAnnotationCounter
import os
import traceback
import random
import csv
import time
import queue

from typing import List, Dict, Tuple
from os.path import join
from tempfile import NamedTemporaryFile
from pathlib import Path
from datetime import timedelta
from joblib import delayed
from multiprocessing import Manager, Process, Queue, managers
from multiprocessing.queues import Queue
from dpu_utils.utils.dataloading import load_jsonl_gz
from libsa4py.cst_extractor import Extractor
from libsa4py.cst_transformers import TypeAnnotationRemover, TypeApplier
from libsa4py.exceptions import ParseError, NullProjectException
from libsa4py.nl_preprocessing import NLPreprocessor
from libsa4py.utils import read_file, list_files, ParallelExecutor, mk_dir_not_exist, save_json, load_json, write_file, \
    create_tmp_file, write_to_tmp_file, delete_tmp_file, mk_dir_cp_file
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
                 dups_files_path=None, split_files_path=None, ignored_files_path=None):
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

        if ignored_files_path is not None:
            self.ignored_files = set(read_file(ignored_files_path).splitlines())
        else:
            self.ignored_files = {}

        if self.use_tc:
            self.tc = MypyManager('mypy', MAX_TC_TIME)

        self.split_dataset_files = {f: s for s, f in
                                    csv.reader(open(split_files_path, 'r'))} if split_files_path is not None else {}

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

        extracted_module['variables'] = {self.nlp_prep.process_identifier(v): t for v, t in
                                         extracted_module['variables'].items()}
        extracted_module['mod_var_occur'] = {v: [self.nlp_prep.process_sentence(j) for i in o for j in i] for v,
                                                                                                              o in
                                             extracted_module['mod_var_occur'].items()}

        for c in extracted_module['classes']:
            c['variables'] = {self.nlp_prep.process_identifier(v): t for v, t in c['variables'].items()}
            c['cls_var_occur'] = {v: [self.nlp_prep.process_sentence(j) for i in o for j in i] for v,
                                                                                                   o in
                                  c['cls_var_occur'].items()}
            c['funcs'] = [fn_nlp_transf(f, self.nlp_prep) for f in c['funcs']]

        extracted_module['funcs'] = [fn_nlp_transf(f, self.nlp_prep) for f in extracted_module['funcs']]

        return extracted_module

    def process_project(self, i, project, project_files: List[str]):

        project_id = f'{project["author"]}/{project["repo"]}'
        project_analyzed_files: dict = {project_id: {"src_files": {}, "type_annot_cove": 0.0}}
        try:
            print(f'Running pipeline for project {i} {project_id}')
            project['files'] = []

            print(f'Extracting for {project_id}...')
            extracted_avl_types = None

            print(f"{project_id} has {len(project_files)} files before deduplication")
            project_files = [f for f in project_files if not self.is_file_duplicate(f)]
            print(f"{project_id} has {len(project_files)} files after deduplication")
            project_files = [f for f in project_files if str(Path(f).relative_to(Path(self.projects_path).parent)) not in self.ignored_files]
            print(f"{project_id} has {len(project_files)} files after ignoring files")

            project_files = [(f, str(Path(f).relative_to(Path(self.projects_path).parent))) for f in project_files]
            project_files = [(f, f_r, self.split_dataset_files[f_r] if f_r in self.split_dataset_files else None) for f,
                                                                                                                      f_r
                             in project_files]

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
                        # print(f"Could not process file {filename}")
                        traceback.print_exc()
                        self.logger.error("project: %s |file: %s |Exception: %s" % (project_id, filename, err))
                        # logging.error("project: %s |file: %s |Exception: %s" % (project_id, filename, err))

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
        repos_list = [(p, *list_files(join(self.projects_path, p["author"], p["repo"]))) \
                      for p in repos_list if not (os.path.exists(self.get_project_filename(p)) and self.use_cache)]
        # Sorts projects based on total size of their files
        repos_list.sort(key=lambda x: x[2], reverse=True)
        print(f"Number of projects to be processed after considering cache: {len(repos_list)}")

        start_t = time.time()
        ParallelExecutor(n_jobs=jobs)(total=len(repos_list))(
            delayed(self.process_project)(i, p, p_files) for i, (p, p_files, p_size) in enumerate(repos_list, start=start))
        print("Finished processing %d projects in %s " % (len(repos_list), str(timedelta(seconds=time.time()-start_t))))

        if self.use_pyre:
            pyre_kill_all_servers()
        logging.shutdown()


class TypeAnnotatingProjects:
    """
    It applies the inferred type annotations to the input dataset
    """

    def __init__(self, projects_path: str, output_path: str, dry_run: bool = False,
                 apply_nlp: bool = True):
        self.projects_path = projects_path
        self.output_path = output_path
        self.dry_run = dry_run
        self.apply_nlp = apply_nlp

    def process_project(self, proj_json_path: str):
        proj_json = load_json(proj_json_path)
        total_added_types = 0
        total_no_types = 0
        for p in proj_json.keys():
            for i, (f, f_d) in enumerate(proj_json[p]['src_files'].items()):
                print(f"Adding types to file {f} from project {proj_json_path}")
                total_no_types += f_d['no_types_annot']['I'] + f_d['no_types_annot']['D']
                if f_d['no_types_annot']['I'] + f_d['no_types_annot']['D'] > 0:
                    f_read = read_file(join(self.projects_path, f))
                    try:
                        f_parsed = cst.parse_module(f_read)
                        try:
                            ta = TypeApplier(f_d, self.apply_nlp)
                            f_parsed = cst.metadata.MetadataWrapper(f_parsed).visit(ta)
                            if not self.dry_run:
                                write_file(join(self.projects_path, f), f_parsed.code)
                            total_added_types += ta.no_applied_types
                            print(f"Applied {ta.no_applied_types} types to file {f} from project {proj_json_path}")
                            assert f_d['no_types_annot']['I'] + f_d['no_types_annot']['D'] <= self.__get_no_applied_types(f_parsed.code) + ta.no_failed_applied_types
                        except KeyError as ke:
                            print(f"A variable not found | project {proj_json_path} | file {f}", ke)
                            traceback.print_exc()
                        except TypeError as te:
                            print(f"Project {proj_json_path} | file {f}", te)
                            traceback.print_exc()
                        except AssertionError as te:
                            print(f"[AssertionError] Project {proj_json_path} | file {f}", te)
                    except cst._exceptions.ParserSyntaxError as pse:
                        print(f"Can't parsed file {f} in project {proj_json_path}", pse)

        return total_added_types, total_no_types

    def run(self, jobs: int):
        proj_jsons, _ = list_files(join(self.output_path, 'processed_projects'), '.json')
        proj_jsons.sort(key=lambda f: os.stat(f).st_size, reverse=True)
        start_t = time.time()
        proj_type_added = ParallelExecutor(n_jobs=jobs)(total=len(proj_jsons))(delayed(self.process_project)(p_j) \
                                                                               for p_j in proj_jsons)
        print(f"Finished applying types in {str(timedelta(seconds=time.time() - start_t))}")
        print(f"{sum([a for a, t in proj_type_added]):,}/{sum([t for a, t in proj_type_added]):,} types applied to the whole dataset")

    def __get_no_applied_types(self, code: str) -> int:
        f_applied_p = cst.parse_module(code)
        tac = TypeAnnotationCounter()
        f_applied_p.visit(tac)
        return tac.total_no_type_annot

class TypeAnnotationsRemoval:
    """
    Removes type annotations that cannot be type-checked by mypy
    """

    MAX_TYPE_ERRORS_PER_FILE = 500

    def __init__(self, input_projects_path: str, output_projects_path: str, processed_projects_path: str, no_projects_limit: int = None,
                 dry_run: bool = False, apply_nlp: bool = True):
        self.input_projects_path = input_projects_path
        self.processed_projects_path = processed_projects_path
        self.output_projects_path = output_projects_path
        self.no_projects_limit = no_projects_limit
        self.dry_run = dry_run
        self.apply_nlp = apply_nlp

    #def process_file(self, f: str, f_d_repr: dict, tc_res: dict):
    def process_file(self, q: Queue, is_f_loader_done, tc_res: dict, ignored_files: list):
        # TODO: The initial type-checking should not be done after adding no. type errors to the representation later on.
        # init_tc, init_no_tc_err = type_check_single_file(join(self.projects_path, f),
        #                                                  MypyManager('mypy', MAX_TC_TIME))

        # if init_tc == False and init_no_tc_err is None:
        #     return
        # else:
        # Only files with type annotations
        while not is_f_loader_done.value or q.qsize() != 0:
            try:
                f, f_d_repr = q.get(True, 1)
                if f_d_repr['no_types_annot']['I'] + f_d_repr['no_types_annot']['D'] > 0:
                    try:
                        #tmp_f = create_tmp_file(".py")
                        f_read = read_file(join(self.output_projects_path, f))
                        _, tc_errs, type_annot_r, tc_errors = self.remove_unchecked_type_annot(join(self.output_projects_path, f),
                                                                                                       f_read, f_d_repr, f_d_repr['tc'][1])
                        print(f"F: {f} | init_tc_errors: {f_d_repr['tc'][1]} | tc_errors: {tc_errs} | ta_r: {type_annot_r} | \
                            total_ta: {f_d_repr['no_types_annot']['I'] + f_d_repr['no_types_annot']['D']} | Queue size: {q.qsize()}")
                        tc_res[f] = {"init_tc_errs": f_d_repr['tc'][1], "curr_tc_errs": tc_errs, "ta_rem": type_annot_r,
                                     "total_ta": f_d_repr["no_types_annot"]['I'] + f_d_repr["no_types_annot"]['D'],
                                     "errors": tc_errors}
                        # Path(join(self.output_path, Path(f).parent)).mkdir(parents=True, exist_ok=True)
                        if tc_errs == 0:
                            if self.dry_run:
                                write_file(join(self.output_projects_path, f), f_read)
                        else:
                            write_file(join(self.output_projects_path, f), f_read)
                            ignored_files.append(f)
                    except Exception as e:
                        print(f"F: {f} | e: {e}")
                        traceback.print_exc()
                    # finally:
                    #     delete_tmp_file(tmp_f)
                else:
                    print(f"F: {f} | init_tc_errors: {f_d_repr['tc'][1]} | total_ta: {f_d_repr['no_types_annot']['I'] + f_d_repr['no_types_annot']['D']} | Queue size: {q.qsize()}")
                    tc_res[f] = {"init_tc_errs": f_d_repr['tc'][1], "curr_tc_errs": f_d_repr['tc'][1], "ta_rem": None,
                                 "total_ta": f_d_repr["no_types_annot"]['I'] + f_d_repr["no_types_annot"]['D'],
                                 "errors": None}
                    ignored_files.append(f)
            except queue.Empty as e:
                print(f"Worker {os.getpid()} finished! Queue's empty!")
                print(f"File loader working {is_f_loader_done.value} and queue size {q.qsize()}")

    def run(self, jobs: int):
        manager = Manager()
        q = manager.Queue()
        is_f_loader_done = manager.Value('i', False)
        ignored_files_a = manager.list()
        type_checked_files = manager.list()
        
        file_loader = Process(target=self.__load_projects_files, args=(q, is_f_loader_done, ignored_files_a,
                                                                       type_checked_files))
        file_loader.start()
        #file_loader.join()

        print("File loader started!")

        # merged_projects = load_json(join(self.processed_projects_path, "merged_all_projects.json"))
        # not_tced_src_f: List[Tuple[str, dict]] = []
        # for p, p_v in list(merged_projects['projects'].items()):
        #     for f, f_v in p_v['src_files'].items():
        #         if not f_v['tc'][0] and f_v['tc'] != [False, None]:
        #             not_tced_src_f.append((f, f_v))

        # del merged_projects
        # # not_tced_src_f = not_tced_src_f[:250]
        # # print("L:", len(not_tced_src_f))
        # manager = Manager()
        time.sleep(5)
        start_t = time.time()
        tc_res = manager.dict()
        ignored_files_b = manager.list()
        file_processors = []
        for j in range(jobs):
            p = Process(target=self.process_file, args=(q, is_f_loader_done, tc_res, ignored_files_b))
            p.daemon = True
            file_processors.append(p)
            p.start()

        for p in file_processors:
            p.join()
        file_loader.join()
        # ParallelExecutor(n_jobs=jobs)(total=0)(delayed(self.process_file)(f, f_d, tc_res) \
        #                                                          for f, f_d in not_tced_src_f)
        print(f"Finished fixing invalid types in {str(timedelta(seconds=time.time() - start_t))}")
        save_json(join(self.processed_projects_path, "tc_ta_results_new.json"), tc_res.copy())
        write_file(join(self.processed_projects_path, 'ignored_files.txt'), '\n'.join(list(ignored_files_a) + list(ignored_files_b)))
        write_file(join(self.processed_projects_path, 'tced_files.txt'), '\n'.join(list(type_checked_files)))
        
    def __load_projects_files(self, q: Queue, is_done, ignored_files: list, type_checked_files: list):
        proj_jsons, _ = list_files(join(self.processed_projects_path, 'processed_projects'), '.json')
        proj_jsons = proj_jsons[:self.no_projects_limit] if self.no_projects_limit is not None else proj_jsons
        f_loaded = 0
        for p_j in proj_jsons:
            proj_json = load_json(p_j)
            for _, p_v in proj_json.items():
                for f, f_v in p_v['src_files'].items():
                    if not f_v['tc'][0]:
                        if f_v['tc'] != [False, None, None]:
                            if f_v['tc'][1] <= TypeAnnotationsRemoval.MAX_TYPE_ERRORS_PER_FILE:
                                mk_dir_cp_file(join('/home/amir/data/MT4Py-pyre-apply', f), join(self.output_projects_path, f))
                                q.put((f, f_v))
                                f_loaded += 1
                                print(f"Added file {f} to the analysis queue")
                            else:
                                ignored_files.append(f)
                        else:
                            ignored_files.append(f)
                    else:
                        type_checked_files.append(f)
                        
                        #print("Adding files to Queue...")
        is_done.value = True
        print(f"Loaded {f_loaded} Python files")

        for f in type_checked_files:
            mk_dir_cp_file(join(self.input_projects_path, f), join(self.output_projects_path, f))
            print(f"Copied type-checked file: {f}")
            
    def remove_unchecked_type_annot(self, f_path: str, f_read: str, f_d_repr: dict,
                                    init_no_tc_err: int) -> Tuple[str, int, List[str]]:

        type_annots_removed: List[str] = []
        no_try = 0
        MAX_TRY = 10

        def type_check_ta(curr_no_tc_err: int,  org_gt):
            tc, no_tc_err, f_code, tc_errors = self.__type_check_type_annotation(f_path, f_read, f_d_repr)
            nonlocal no_try
            if no_tc_err is not None:
                if tc:
                    type_annots_removed.append(org_gt)
                elif no_tc_err < curr_no_tc_err:
                    curr_no_tc_err = no_tc_err
                    type_annots_removed.append(org_gt)
                else:
                    no_try += 1
            else:
                no_try += 1

            return tc, no_tc_err, f_code, tc_errors

        out_f_code: str = ""
        tc_errors = None
        for m_v, m_v_t in f_d_repr['variables'].items():
            if m_v_t != "":
                print(f"Type-checking module-level variable {m_v} with annotation {m_v_t}")
                f_d_repr['variables'][m_v] = ""
                # tc, no_tc_err, f_code = self.__type_check_type_annotation(f_read, f_d_repr, f_out_temp)
                # if tc:
                #     type_annots_removed.append(m_v_t)
                #     return f_code, no_tc_err, type_annots_removed
                # elif no_tc_err < init_no_tc_err:
                #     out_f_code = f_code
                #     init_no_tc_err = no_tc_err
                #     type_annots_removed.append(m_v_t)
                # elif no_tc_err == init_no_tc_err:
                #     f_d_repr['variables'][m_v] = m_v_t
                tc, no_tc_err, out_f_code, tc_errors = type_check_ta(init_no_tc_err, m_v_t)
                if tc or no_try > MAX_TRY:
                    return out_f_code, no_tc_err, type_annots_removed, tc_errors
                else:
                    f_d_repr['variables'][m_v] = m_v_t

        for i, fn in enumerate(f_d_repr['funcs']):
            for p_n, p_t in fn['params'].items():
                if p_t != "":
                    print(f"Type-checking function parameter {p_n} with annotation {p_t}")
                    f_d_repr['funcs'][i]['params'][p_n] = ""
                    # tc, no_tc_err, f_code = self.__type_check_type_annotation(f_read, f_d_repr, f_out_temp)
                    # if tc:
                    #     type_annots_removed.append(p_t)
                    #     return f_code, no_tc_err, type_annots_removed
                    # elif no_tc_err < init_no_tc_err:
                    #     out_f_code = f_code
                    #     init_no_tc_err = no_tc_err
                    #     type_annots_removed.append(p_t)
                    # elif no_tc_err == init_no_tc_err:
                    #     f_d_repr['funcs'][i]['params'][p_n] = p_t
                    tc, no_tc_err, out_f_code, tc_errors = type_check_ta(init_no_tc_err, p_t)
                    if tc or no_try > MAX_TRY:
                        return out_f_code, no_tc_err, type_annots_removed, tc_errors
                    else:
                        f_d_repr['funcs'][i]['params'][p_n] = p_t

            for fn_v, fn_v_t in fn['variables'].items():
                if fn_v_t != "":
                    print(f"Type-checking function variable {fn_v} with annotation {fn_v_t}")
                    f_d_repr['funcs'][i]['variables'][fn_v] = ""
                    # tc, no_tc_err, f_code = self.__type_check_type_annotation(f_read, f_d_repr, f_out_temp)
                    # if tc:
                    #     type_annots_removed.append(fn_v_t)
                    #     return f_code, no_tc_err, type_annots_removed
                    # elif no_tc_err < init_no_tc_err:
                    #     out_f_code = f_code
                    #     init_no_tc_err = no_tc_err
                    #     type_annots_removed.append(fn_v_t)
                    # elif no_tc_err == init_no_tc_err:
                    #     f_d_repr['funcs'][i]['variables'][fn_v] = fn_v_t
                    tc, no_tc_err, out_f_code, tc_errors = type_check_ta(init_no_tc_err, fn_v_t)
                    if tc or no_try > MAX_TRY:
                        return out_f_code, no_tc_err, type_annots_removed, tc_errors
                    else:
                        f_d_repr['funcs'][i]['variables'][fn_v] = fn_v_t

            # The return type for module-level functions
            if f_d_repr['funcs'][i]['ret_type'] != "":
                org_t = f_d_repr['funcs'][i]['ret_type']
                print(f"Type-checking function {f_d_repr['funcs'][i]['name']} return with {org_t}")
                f_d_repr['funcs'][i]['ret_type'] = ""
                # tc, no_tc_err, f_code = self.__type_check_type_annotation(f_read, f_d_repr, f_out_temp)
                # if tc:
                #     type_annots_removed.append(org_t)
                #     return f_code, no_tc_err, type_annots_removed
                # elif no_tc_err < init_no_tc_err:
                #     out_f_code = f_code
                #     init_no_tc_err = no_tc_err
                #     type_annots_removed.append(org_t)
                # elif no_tc_err == init_no_tc_err:
                #     f_d_repr['funcs'][i]['ret_type'] = org_t
                tc, no_tc_err, out_f_code, tc_errors = type_check_ta(init_no_tc_err, org_t)
                if tc or no_try > MAX_TRY:
                    return out_f_code, no_tc_err, type_annots_removed, tc_errors
                else:
                    f_d_repr['funcs'][i]['ret_type'] = org_t

        # The type of class-level vars
        for c_i, c in enumerate(f_d_repr['classes']):
            for c_v, c_v_t in c['variables'].items():
                if c_v_t != "":
                    print(f"Type checking class variable {c_v} with annotation {c_v_t}")
                    f_d_repr['classes'][c_i]['variables'][c_v] = ""
                    # tc, no_tc_err, f_code = self.__type_check_type_annotation(f_read, f_d_repr, f_out_temp)
                    # if tc:
                    #     type_annots_removed.append(c_v_t)
                    #     return f_code, no_tc_err, type_annots_removed
                    # elif no_tc_err < init_no_tc_err:
                    #     out_f_code = f_code
                    #     init_no_tc_err = no_tc_err
                    #     type_annots_removed.append(c_v_t)
                    # elif no_tc_err == init_no_tc_err:
                    #     f_d_repr['classes'][c_i]['variables'][c_v] = c_v_t
                    tc, no_tc_err, out_f_code, tc_errors = type_check_ta(init_no_tc_err, c_v_t)
                    if tc or no_try > MAX_TRY:
                        return out_f_code, no_tc_err, type_annots_removed, tc_errors
                    else:
                        f_d_repr['classes'][c_i]['variables'][c_v] = c_v_t

            # The type of arguments for class-level functions
            for fn_i, fn in enumerate(c['funcs']):
                for p_n, p_t in fn["params"].items():
                    if p_t != "":
                        print(f"Type-checking function parameter {p_n} with annotation {p_t}")
                        f_d_repr['classes'][c_i]['funcs'][fn_i]['params'][p_n] = ""
                        # tc, no_tc_err, f_code = self.__type_check_type_annotation(f_read, f_d_repr, f_out_temp)
                        # if tc:
                        #     type_annots_removed.append(p_t)
                        #     return f_code, no_tc_err, type_annots_removed
                        # elif no_tc_err < init_no_tc_err:
                        #     out_f_code = f_code
                        #     init_no_tc_err = no_tc_err
                        #     type_annots_removed.append(p_t)
                        # elif no_tc_err == init_no_tc_err:
                        #     f_d_repr['classes'][c_i]['funcs'][fn_i]['params'][p_n] = p_t
                        tc, no_tc_err, out_f_code, tc_errors = type_check_ta(init_no_tc_err, p_t)
                        if tc or no_try > MAX_TRY:
                            return out_f_code, no_tc_err, type_annots_removed, tc_errors
                        else:
                            f_d_repr['classes'][c_i]['funcs'][fn_i]['params'][p_n] = p_t

                # The type of local variables for class-level functions
                for fn_v, fn_v_t in fn['variables'].items():
                    if fn_v_t != "":
                        print(f"Type-checking function variable {fn_v} with annotation {fn_v_t}")
                        f_d_repr['classes'][c_i]['funcs'][fn_i]['variables'][fn_v] = ""
                        # tc, no_tc_err, f_code = self.__type_check_type_annotation(f_read, f_d_repr, f_out_temp)
                        # if tc:
                        #     type_annots_removed.append(fn_v_t)
                        #     return f_code, no_tc_err, type_annots_removed
                        # elif no_tc_err < init_no_tc_err:
                        #     out_f_code = f_code
                        #     init_no_tc_err = no_tc_err
                        #     type_annots_removed.append(fn_v_t)
                        # elif no_tc_err == init_no_tc_err:
                        #     f_d_repr['classes'][c_i]['funcs'][fn_i]['variables'][fn_v] = fn_v_t
                        tc, no_tc_err, out_f_code, tc_errors = type_check_ta(init_no_tc_err, fn_v_t)
                        if tc or no_try > MAX_TRY:
                            return out_f_code, no_tc_err, type_annots_removed, tc_errors
                        else:
                            f_d_repr['classes'][c_i]['funcs'][fn_i]['variables'][fn_v] = fn_v_t

                # The return type for class-level functions
                if f_d_repr['classes'][c_i]['funcs'][fn_i]['ret_type'] != "":
                    org_t = f_d_repr['classes'][c_i]['funcs'][fn_i]['ret_type']
                    print(
                        f"Annotating function {f_d_repr['classes'][c_i]['funcs'][fn_i]['name']} return with type {org_t}")
                    f_d_repr['classes'][c_i]['funcs'][fn_i]['ret_type'] = ""
                    # tc, no_tc_err, f_code = self.__type_check_type_annotation(f_read, f_d_repr, f_out_temp)
                    # if tc:
                    #     type_annots_removed.append(org_t)
                    #     return f_code, no_tc_err, type_annots_removed
                    # elif no_tc_err < init_no_tc_err:
                    #     out_f_code = f_code
                    #     init_no_tc_err = no_tc_err
                    #     type_annots_removed.append(org_t)
                    # elif no_tc_err == init_no_tc_err:
                    #     f_d_repr['classes'][c_i]['funcs'][fn_i]['ret_type'] = org_t
                    tc, no_tc_err, out_f_code, tc_errors = type_check_ta(init_no_tc_err, org_t)
                    if tc or no_try > MAX_TRY:
                        return out_f_code, no_tc_err, type_annots_removed, tc_errors
                    else:
                        f_d_repr['classes'][c_i]['funcs'][fn_i]['ret_type'] = org_t

        return out_f_code, init_no_tc_err, type_annots_removed, tc_errors

    def __type_check_type_annotation(self, f_path: str, f_read: str, f_d_repr: dict):
        f_t_applied = cst.metadata.MetadataWrapper(cst.parse_module(f_read)).visit(TypeApplier(f_d_repr,
                                                                                               apply_nlp=self.apply_nlp))
        
        # Writing applied code to temp files has an advantage which isolates the file and as a result, 
        # type-checking may be successful for some failed cases with the original file
        # tmp_f = create_tmp_file(".py")
        # write_to_tmp_file(tmp_f, f_t_applied.code)
        write_file(f_path, f_t_applied.code)
        tc, no_tc_err, tc_errors = type_check_single_file(f_path, MypyManager('mypy', MAX_TC_TIME))
        #delete_tmp_file(tmp_f)
        return tc, no_tc_err, f_t_applied.code, tc_errors
