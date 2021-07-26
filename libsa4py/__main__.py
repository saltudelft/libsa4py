from argparse import ArgumentParser
from multiprocessing import cpu_count
from libsa4py.utils import find_repos_list
from libsa4py.cst_pipeline import Pipeline, TypeAnnotatingProjects, TypeAnnotationsRemoval
from libsa4py.merge import merge_projects


def process_projects(args):
    input_repos = find_repos_list(args.p) if args.l is None else find_repos_list(args.p)[:args.l]
    p = Pipeline(args.p, args.o, not args.no_nlp, args.use_cache, args.use_pyre, args.use_tc, args.d, args.s)
    p.run(input_repos, args.j)


def apply_types_projects(args):
    tap = TypeAnnotatingProjects(args.p, args.o, args.dry_run)
    tap.run(args.j)


def remove_err_type_annotations(args):
    tar = TypeAnnotationsRemoval(args.p, args.o, "")
    tar.run(args.j)


def main():

    arg_parser = ArgumentParser(description="Light-weight static analysis to extract Python's code representations")
    sub_parsers = arg_parser.add_subparsers(dest='cmd')

    process_parser = sub_parsers.add_parser('process')
    process_parser.add_argument("--p", required=True, type=str, help="Path to Python projects")
    process_parser.add_argument("--o", required=True, type=str, help="Path to store JSON-based processed projects")
    process_parser.add_argument("--d", "--deduplicate", required=False, type=str, help="Path to duplicate files")
    process_parser.add_argument("--s", "--split", required=False, type=str, help="Path to the dataset split files")
    process_parser.add_argument("--j", default=cpu_count(), type=int, help="Number of workers for processing projects")
    process_parser.add_argument("--l", required=False, type=int, help="Number of projects to process")
    process_parser.add_argument("--c", "--cache", dest='use_cache', action='store_true', help="Whether to ignore processed projects")
    process_parser.add_argument("--no-nlp", dest='no_nlp', action='store_true', help="Whether to apply standard NLP "
                                                                                 "techniques to extracted identifiers")
    process_parser.add_argument("--pyre", dest='use_pyre', action='store_true',
                                help="Whether to run pyre to infer types of variables in files")
    process_parser.add_argument("--tc", dest='use_tc', action='store_true',
                                help="Whether to type-check type annotations in projects")

    process_parser.set_defaults(no_nlp=False)
    process_parser.set_defaults(use_cache=False)
    process_parser.set_defaults(use_pyre=False)
    process_parser.set_defaults(use_tc=False)
    process_parser.set_defaults(func=process_projects)

    merge_parser = sub_parsers.add_parser('merge')
    merge_parser.add_argument("--o", required=True, type=str, help="Path to store JSON-based processed projects")
    merge_parser.add_argument("--l", required=False, type=int, help="Number of projects to be merged")
    merge_parser.set_defaults(func=merge_projects)

    apply_parser = sub_parsers.add_parser('apply')
    apply_parser.add_argument("--p", required=True, type=str, help="Path to Python projects")
    apply_parser.add_argument("--o", required=True, type=str, help="Path to store JSON-based processed projects")
    apply_parser.add_argument("--j", default=cpu_count(), type=int, help="Number of workers for processing projects")
    apply_parser.add_argument("--d", dest='dry_run', action='store_true',
                                help="Dry run does not apply types to the dataset's files")

    apply_parser.set_defaults(dry_run=False)
    apply_parser.set_defaults(func=apply_types_projects)

    remove_parser = sub_parsers.add_parser('remove')
    remove_parser.add_argument("--p", required=True, type=str, help="Path to Python projects")
    remove_parser.add_argument("--o", required=True, type=str, help="Path to store JSON-based processed projects")
    remove_parser.add_argument("--j", default=cpu_count(), type=int, help="Number of workers for processing files")
    remove_parser.set_defaults(func=remove_err_type_annotations)

    args = arg_parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
