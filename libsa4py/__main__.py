from argparse import ArgumentParser
from multiprocessing import cpu_count
from libsa4py.utils import find_repos_list
from libsa4py.cst_pipeline import Pipeline
from libsa4py.merge import merge_projects


def process_projects(args):
    input_repos = find_repos_list(args.p) if args.l is None else find_repos_list(args.p)[:args.l]
    print(len(input_repos))
    p = Pipeline(args.p, input_repos, args.o, not args.no_nlp, args.use_cache, args.d, args.s)
    p.run(input_repos, args.j)


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
    process_parser.set_defaults(no_nlp=False)
    process_parser.set_defaults(use_cache=False)
    process_parser.set_defaults(func=process_projects)

    merge_parser = sub_parsers.add_parser('merge')
    merge_parser.add_argument("--o", required=True, type=str, help="Path to store JSON-based processed projects")
    merge_parser.set_defaults(func=merge_projects)

    args = arg_parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
