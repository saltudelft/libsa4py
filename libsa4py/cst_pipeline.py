import json
import os
import traceback
import random

from os.path import join
from pathlib import Path
from joblib import delayed
from dpu_utils.utils.dataloading import load_jsonl_gz
from libsa4py.cst_extractor import Extractor
from libsa4py.exceptions import ParseError
from libsa4py.nl_preprocessing import NLPreprocessor
from libsa4py.utils import filter_directory, read_file, list_files, ParallelExecutor, mk_dir_not_exist

import logging
import logging.config

# Create output directory
if not os.path.isdir('./output'):
    os.mkdir('./output')


class Pipeline:
    """
    This is the new pipeline that converts a project to the output JSON of LibCST analysis
    """

    def __init__(self, projects_path, input_projects, output_dir, nlp_transf: bool = True,
                 use_cache: bool = True, dups_files_path=None):
        self.projects_path = projects_path
        self.input_projects = input_projects
        self.output_dir = output_dir
        self.processed_projects = None
        self.err_log_dir = None
        self.avl_types_dir = None
        self.nlp_transf = nlp_transf
        self.use_cache = use_cache
        self.nlp_prep = NLPreprocessor()

        self.__make_output_dirs()

        if dups_files_path is not None:
            clusters_rand_files = [l.pop(random.randrange(len(l))) for l in load_jsonl_gz(dups_files_path)]
            self.duplicate_files = [f for l in load_jsonl_gz(dups_files_path) for f in l]
            self.duplicate_files = set(self.duplicate_files).difference(set(clusters_rand_files))
            self.is_file_duplicate = lambda x: True if x in self.duplicate_files else False
        else:
            self.is_file_duplicate = lambda x: False

        # TODO: Fix the logger issue not outputing the logs into the file.
        logging.basicConfig(filename=join(self.err_log_dir, "pipeline_errors.log"), level=logging.DEBUG,
                            format='%(asctime)s %(name)s %(message)s')
        self.logger = logger = logging.getLogger(__name__)
        # self.logger = self.__setup_pipeline_logger(join(self.err_log_dir, "pipeline_errors.log"))

    def __make_output_dirs(self):
        mk_dir_not_exist(self.output_dir)

        self.processed_projects = join(self.output_dir, "processed_projects")
        self.avl_types_dir = join(self.output_dir, "extracted_visible_types")
        self.err_log_dir = join(self.output_dir, "error_logs")
        mk_dir_not_exist(self.processed_projects)
        mk_dir_not_exist(self.avl_types_dir)
        mk_dir_not_exist(self.err_log_dir)

    # def __setup_pipeline_logger(self, log_dir: str):
    #     logger = logging.getLogger(__name__)
    #     logger.setLevel(logging.DEBUG)
    #
    #     logger_handler = logging.FileHandler(filename=log_dir)
    #     logger_handler.setLevel(logging.DEBUG)
    #
    #     logger_formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
    #     logger_handler.setFormatter(logger_formatter)
    #
    #     logger.addHandler(logger_handler)
    #
    #     return logger

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
            fn_d['params_descr'] = {nlp_prep.process_identifier(p): nlp_prep.process_sentence(fn_d['params_descr'][p]) \
                                    for p in fn_d['params_descr'].keys()}
            fn_d['docstring']['func'] = nlp_prep.process_sentence(fn_d['docstring']['func'])
            fn_d['docstring']['ret'] = nlp_prep.process_sentence(fn_d['docstring']['ret'])
            fn_d['docstring']['long_descr'] = nlp_prep.process_sentence(fn_d['docstring']['long_descr'])
            return fn_d

        extracted_module['variables'] = {self.nlp_prep.process_identifier(v): t for v, t in extracted_module['variables'].items()}

        for c in extracted_module['classes']:
            c['variables'] = {self.nlp_prep.process_identifier(v): t for v, t in c['variables'].items()}
            c['funcs'] = [fn_nlp_transf(f, self.nlp_prep) for f in c['funcs']]

        extracted_module['funcs'] = [fn_nlp_transf(f, self.nlp_prep) for f in extracted_module['funcs']]

        return extracted_module

    def process_project(self, i, project):

        project_id = f'{project["author"]}/{project["repo"]}'
        project_analyzed_files: dict = {project_id: {"src_files": {}}}
        try:
            print(f'Running pipeline for project {i} {project_id}')
            project['files'] = []

            print(f'Filtering for {project_id}...')
            print(join(self.output_dir, project["author"], project["repo"]))
            filtered_project_directory = filter_directory(join(self.projects_path, project["author"], project["repo"]))
            print(f'Extracting for {project_id}...')
            extracted_avl_types = None

            project_files = list_files(filtered_project_directory)
            print(f"{project_id} has {len(project_files)} files before deduplication")
            project_files = [f for f in project_files if not self.is_file_duplicate(f)]
            print(f"{project_id} has {len(project_files)} files after deduplication")

            for filename in project_files:
                f_relative = str(Path(filename).relative_to(Path(self.projects_path).parent))
                try:
                    project_analyzed_files[project_id]["src_files"][f_relative] = \
                        self.apply_nlp_transf(Extractor().extract(read_file(filename))) if self.nlp_transf \
                            else Extractor.extract(read_file(filename))
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
                    print(f"Could not process file {filename}")
                    traceback.print_exc()
                    #self.logger.error("project: %s |file: %s |Exception: %s" % (project_id, filename, err))
                    #logging.error("project: %s |file: %s |Exception: %s" % (project_id, filename, err))

            print(f'Saving available type hints for {project_id}...')

            if self.avl_types_dir is not None:
                if extracted_avl_types:
                    with open(join(self.avl_types_dir, f'{project["author"]}_{project["repo"]}_avltypes.txt'),
                              'w') as f:
                        for t in extracted_avl_types:
                            f.write("%s\n" % t)
        except KeyboardInterrupt:
            quit(1)
        except Exception as err:
            print(f'Running pipeline for project {i} failed')
            traceback.print_exc()
            self.logger.debug("project: %s | Exception: %s" % (project_id, err))
            #logging.error("project: %s | Exception: %s" % (project_id, err))
        finally:
            try:
                with open(self.get_project_filename(project), 'w') as p_json_f:
                    json.dump(project_analyzed_files, p_json_f, indent=4)
            except Exception as err:
                self.logger.error(
                    "project: %s | Exception: %s | json: %s" % (project_id, err, str(project_analyzed_files)))

    def run(self, repos_list, jobs, start=0):

        print(f"Number of projects to be processed: {len(repos_list)}")
        repos_list = [p for p in repos_list if not (os.path.exists(self.get_project_filename(p)) and self.use_cache)]
        print(f"Number of projects to be processed after considering cache: {len(repos_list)}")

        ParallelExecutor(n_jobs=jobs)(total=len(repos_list))(
            delayed(self.process_project)(i, project) for i, project in enumerate(repos_list, start=start))
