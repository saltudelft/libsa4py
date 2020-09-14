import argparse
import json
import os
import time
import traceback
import logging

from joblib import delayed
from libsa4py.cst_extractor import Extractor
from libsa4py.exceptions import ParseError
from libsa4py.nl_preprocessing import NLPreprocessor
from libsa4py.utils import filter_directory, read_file, list_files
from libsa4py.utils import ParallelExecutor


# Create output directory
if not os.path.isdir('./output'):
    os.mkdir('./output')


class Pipeline:
    """
    This is the new pipeline that converts a project to the output JSON of LibCST analysis
    """

    def __init__(self, repos_dir, output_dir, err_log_dir, avl_types_dir=None, nlp_tansf: bool = True,
                 use_cache: bool = True):
        self.repos_dir = repos_dir
        self.output_dir = output_dir
        self.err_log_dir = err_log_dir
        self.avl_types_dir = avl_types_dir
        self.nlp_transf = nlp_tansf

        logging.basicConfig(filename=os.path.join(self.err_log_dir, "pipline_erros.log"), level=logging.DEBUG,
                            format='%(asctime)s %(name)s %(message)s')
        self.logger = logging.getLogger(__name__)
        self.use_cache = use_cache

        self.nlp_prep = NLPreprocessor()

    def get_project_filename(self, project) -> str:
        """
        Return the filename at which a project datafile should be stored.
        :param project: the project dict
        :return: return filename
        """
        return os.path.join(self.output_dir, f"{project['author']}{project['repo']}.json")

    def apply_nlp_transf(self, extracted_module: dict):
        """
        Applies NLP transformation to identifiers in a module
        """

        def fn_nlp_transf(fn_d: dict, nlp_prep: NLPreprocessor):
            fn_d['name'] = nlp_prep.process_identifier(fn_d['name'])
            fn_d['params'] = {nlp_prep.process_identifier(p): t for p, t in fn_d['params']}
            fn_d['ret_exprs'] = [nlp_prep.process_identifier(r.replace('return ', '')) for r in fn_d['ret_exprs']]
            fn_d['params_occur'] = {p: [nlp_prep.process_sentence(j) for i in o for j in i] for p, o in
                                    fn_d['params_occur']}
            fn_d['variables'] = {nlp_prep.process_identifier(v): t for v, t in fn_d['variables']}
            fn_d['params_descr'] = {nlp_prep.process_identifier(p): nlp_prep.process_sentence(fn_d['params_descr'][p]) \
                                    for p in fn_d['params_descr'].keys()}
            fn_d['docstring']['func'] = nlp_prep.process_sentence(fn_d['docstring']['func'])
            fn_d['docstring']['ret'] = nlp_prep.process_sentence(fn_d['docstring']['ret'])
            fn_d['docstring']['long_descr'] = nlp_prep.process_sentence(fn_d['docstring']['long_descr'])
            return fn_d

        extracted_module['variables'] = {self.nlp_prep.process_identifier(v): t for v, t in extracted_module['variables']}

        for c in extracted_module['classes']:
            c['variables'] = {self.nlp_prep.process_identifier(v): t for v, t in c['variables']}
            c['funcs'] = [fn_nlp_transf(f, self.nlp_prep) for f in c['funcs']]

        extracted_module['funcs'] = [fn_nlp_transf(f, self.nlp_prep) for f in extracted_module['funcs']]

        return extracted_module

    def process_project(self, i, project):

        project_id = f'{project["author"]}/{project["repo"]}'
        project_analyzed_files: dict = {project_id: {"src_files": {}}}
        try:
            print(f'Running pipeline for project {i} {project_id}')

            if os.path.exists(self.get_project_filename(project)) and self.use_cache:
                print(f"Found cached copy for project {project_id}")
                return

            project['files'] = []

            print(f'Filtering for {project_id}...')
            filtered_project_directory = filter_directory(os.path.join(self.repos_dir, project["author"],
                                                                       project["repo"]))

            print(f'Extracting for {project_id}...')
            extracted_avl_types = None
            for filename in list_files(filtered_project_directory):
                try:

                    project_analyzed_files[project_id]["src_files"][filename] = \
                        self.apply_nlp_transf(Extractor().extract(read_file(filename))) if self.nlp_transf \
                            else Extractor.extract(read_file(filename))
                    extracted_avl_types = project_analyzed_files[project_id]["src_files"][filename]['imports'] + \
                                          [c['name'] for c in
                                           project_analyzed_files[project_id]["src_files"][filename]['classes']]
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

            print(f'Saving available type hints for {project_id}...')

            if self.avl_types_dir is not None:
                if extracted_avl_types:
                    with open(os.path.join(self.avl_types_dir, f'{project["author"]}_{project["repo"]}_avltypes.txt'),
                              'w') as f:
                        for t in extracted_avl_types:
                            f.write("%s\n" % t)
        except KeyboardInterrupt:
            quit(1)
        except Exception as err:
            print(f'Running pipeline for project {i} failed')
            traceback.print_exc()
            self.logger.error("project: %s | Exception: %s" % (project_id, err))
        finally:
            try:
                with open(self.get_project_filename(project), 'w') as p_json_f:
                    json.dump(project_analyzed_files, p_json_f, indent=4)
            except Exception as err:
                self.logger.error(
                    "project: %s | Exception: %s | json: %s" % (project_id, err, str(project_analyzed_files)))

    def run(self, repos_list, jobs, start=0):
        ParallelExecutor(n_jobs=jobs)(total=len(repos_list))(
            delayed(self.process_project)(i, project) for i, project in enumerate(repos_list, start=start))


# Parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--projects_file',
                    help='json file containing GitHub projects',
                    type=str,
                    default='../resources/mypy-dependents-by-stars.json')
parser.add_argument('--limit',
                    help='limit the number of projects for which the pipeline should run',
                    type=int,
                    default=0)
parser.add_argument("--jobs",
                    help="number of jobs to use for pipeline.",
                    type=int,
                    default=-1)
parser.add_argument("--output_dir",
                    help="output dir for the pipeline",
                    type=str,
                    default=os.path.join('../output', str(int(time.time()))))
parser.add_argument('--start',
                    help='start position within projects list',
                    type=int,
                    default=0)

if __name__ == '__main__':
    # Parse args
    args = parser.parse_args()

    # Create output dir
    OUTPUT_DIRECTORY = args.output_dir
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.mkdir(OUTPUT_DIRECTORY)

    # Open projects file and run pipeline
    with open(args.projects_file) as json_file:
        projects = json.load(json_file)

        if args.limit > 0:
            projects = projects[:args.limit]

        # run_pipeline(projects)
