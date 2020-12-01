from argparse import ArgumentParser
from multiprocessing import cpu_count
from libsa4py.utils import find_repos_list
from libsa4py.cst_pipeline import Pipeline


def main():

    arg_parser = ArgumentParser(description="Light-weight static analysis to extract Python's code representations")
    arg_parser.add_argument("--p", required=True, type=str, help="Path to Python projects")
    arg_parser.add_argument("--o", required=True, type=str, help="Path to store JSON-based processed projects")
    arg_parser.add_argument("--d", "--deduplicate", required=False, type=str, help="Path to duplicate files")
    arg_parser.add_argument("--j", default=cpu_count(), type=int, help="Number of workers for processing projects")
    arg_parser.add_argument("--l", required=False, type=int, help="Number of projects to process")
    arg_parser.add_argument("--no-nlp", dest='no_nlp', action='store_true', help="Whether to apply standard NLP "
                                                                                 "techniques to extracted identifiers")
    arg_parser.set_defaults(no_nlp=False)

    args = arg_parser.parse_args()
    input_repos = find_repos_list(args.p) if args.l is None else find_repos_list(args.p)[:args.l]
    print(len(input_repos))

    p = Pipeline(args.p, input_repos, args.o, not args.no_nlp, True, args.d)
    p.run(input_repos, args.j)


if __name__ == '__main__':
    main()
