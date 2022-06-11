from argparse import ArgumentParser
from importlib.metadata import requires
from multiprocessing import cpu_count

from numpy import number, require
from libsa4py.mt4py_pipeline import (
    Mt4PyApplyTypesSourcecode,
    Mt4pyApplyPredictionMethod,
    Mt4pyApplyTypecheck,
    Mt4pyEvaluate,
    Mt4pyPredictProjects,
)
from libsa4py.utils import find_repos_list
from libsa4py.cst_pipeline import Pipeline, TypeAnnotatingProjects
from libsa4py.merge import merge_projects


def process_projects(args):
    input_repos = (
        find_repos_list(args.p) if args.l is None else find_repos_list(args.p)[: args.l]
    )
    p = Pipeline(
        args.p,
        args.o,
        not args.no_nlp,
        args.use_cache,
        args.use_pyre,
        args.use_tc,
        args.d,
        args.s,
    )
    p.run(input_repos, args.j)


def apply_types_projects(args):
    tap = TypeAnnotatingProjects(args.p, args.o)
    tap.run(args.j)


def mt4py_predict_projects(args):
    print("predicting projects...")
    mt4py_pp = Mt4pyPredictProjects(args.s, args.o, args.m, args.l)
    mt4py_pp.run()


def mt4py_apply_prediction_method(args):
    print("Applying prediction method...")
    mt4py_apm = Mt4pyApplyPredictionMethod(args.m, args.s, args.t, args.o)
    mt4py_apm.run()


def mt4py_apply_types_sourcecode(args):
    print("Applying types to source code..")
    mt4py_ats = Mt4PyApplyTypesSourcecode(args.p, args.s, args.o, args.l)
    mt4py_ats.run()


def mt4py_apply_type_check(args):
    print("Applying type check...")
    mt4py_atc = Mt4pyApplyTypecheck(args.s, args.r, args.l)
    mt4py_atc.run()


def mt4py_evaluate(args):
    print("Evaluating Type4Py's predictions")
    mt4py_eval = Mt4pyEvaluate(args.f, args.t, args.n, args.l)
    mt4py_eval.run()


def main():

    arg_parser = ArgumentParser(
        description="Light-weight static analysis to extract Python's code representations"
    )
    sub_parsers = arg_parser.add_subparsers(dest="cmd")

    process_parser = sub_parsers.add_parser("process")
    process_parser.add_argument(
        "--p", required=True, type=str, help="Path to Python projects"
    )
    process_parser.add_argument(
        "--o",
        required=True,
        type=str,
        help="Path to store JSON-based processed projects",
    )
    process_parser.add_argument(
        "--d", "--deduplicate", required=False, type=str, help="Path to duplicate files"
    )
    process_parser.add_argument(
        "--s",
        "--split",
        required=False,
        type=str,
        help="Path to the dataset split files",
    )
    process_parser.add_argument(
        "--j",
        default=cpu_count(),
        type=int,
        help="Number of workers for processing projects",
    )
    process_parser.add_argument(
        "--l", required=False, type=int, help="Number of projects to process"
    )
    process_parser.add_argument(
        "--c",
        "--cache",
        dest="use_cache",
        action="store_true",
        help="Whether to ignore processed projects",
    )
    process_parser.add_argument(
        "--no-nlp",
        dest="no_nlp",
        action="store_true",
        help="Whether to apply standard NLP " "techniques to extracted identifiers",
    )
    process_parser.add_argument(
        "--pyre",
        dest="use_pyre",
        action="store_true",
        help="Whether to run pyre to infer types of variables in files",
    )
    process_parser.add_argument(
        "--tc",
        dest="use_tc",
        action="store_true",
        help="Whether to type-check type annotations in projects",
    )

    process_parser.set_defaults(no_nlp=False)
    process_parser.set_defaults(use_cache=False)
    process_parser.set_defaults(use_pyre=False)
    process_parser.set_defaults(use_tc=False)
    process_parser.set_defaults(func=process_projects)

    merge_parser = sub_parsers.add_parser("merge")

    merge_parser.add_argument(
        "--l", required=False, type=int, help="Number of projects to be merged"
    )
    merge_parser.add_argument(
        "--o",
        required=True,
        type=str,
        help="Path to store JSON-based processed projects",
    )
    merge_parser.set_defaults(func=merge_projects)

    apply_parser = sub_parsers.add_parser("apply")
    apply_parser.add_argument(
        "--p", required=True, type=str, help="Path to Python projects"
    )
    apply_parser.add_argument(
        "--o",
        required=True,
        type=str,
        help="Path to store JSON-based processed projects",
    )
    apply_parser.add_argument(
        "--j",
        default=cpu_count(),
        type=int,
        help="Number of workers for processing projects",
    )
    apply_parser.set_defaults(func=apply_types_projects)

    # MyType4Py
    # Evaluate predictions
    mt4py_eval_parser = sub_parsers.add_parser("mt4py_eval")
    mt4py_eval_parser.add_argument(
        "--f", required=True, type=str, help="Foldername of filestats"
    )
    mt4py_eval_parser.add_argument(
        "--t", required=True, type=str, help="Foldername of typecheck results"
    )
    mt4py_eval_parser.add_argument(
        "--n", required=True, type=str, help="name of evaluation"
    )
    mt4py_eval_parser.add_argument(
        "--l", required=False, type=int, default=-1, help="limit of files to process"
    )
    mt4py_eval_parser.set_defaults(func=mt4py_evaluate)
    # Apply types to source code
    mt4py_ats_parser = sub_parsers.add_parser("mt4py_ats")
    mt4py_ats_parser.add_argument(
        "--p", required=True, type=str, help="Path to prediction folder"
    )
    mt4py_ats_parser.add_argument(
        "--s", required=True, type=str, help="Path to source code folder"
    )
    mt4py_ats_parser.add_argument(
        "--o", required=True, type=str, help="Path to output folder of applied types"
    )

    mt4py_ats_parser.add_argument("--l", required=False, type=int, help="Limit")
    mt4py_ats_parser.set_defaults(func=mt4py_apply_types_sourcecode)
    # Apply type check
    mt4py_atc_parser = sub_parsers.add_parser("mt4py_atc")
    mt4py_atc_parser.add_argument(
        "--s", required=True, type=str, help="Path to sourcode folder"
    )
    mt4py_atc_parser.add_argument(
        "--l", required=False, type=int, help="limit of files to typecheck"
    )
    mt4py_atc_parser.add_argument(
        "--r", required=True, type=str, help="folder in tc_results"
    )
    mt4py_atc_parser.set_defaults(func=mt4py_apply_type_check)
    # apply prediction method
    mt4py_apm_parser = sub_parsers.add_parser("mt4py_apm")
    mt4py_apm_parser.add_argument(
        "--m", required=True, type=str, help="Apply prediction method"
    )
    mt4py_apm_parser.add_argument(
        "--s", required=True, type=str, help="prediction source folder"
    )
    mt4py_apm_parser.add_argument(
        "--t",
        required=True,
        type=float,
        help="Minimal treshold to apply prediction method",
    )
    mt4py_apm_parser.add_argument(
        "--o",
        required=True,
        type=str,
        help="name of output folder (this method will save the applied prediction method in ./prediction_methods and the filestats in ./filestats",
    )
    mt4py_apm_parser.set_defaults(func=mt4py_apply_prediction_method)

    mt4py_predict_parser = sub_parsers.add_parser("mt4py_predict")
    mt4py_predict_parser.add_argument(
        "--s",
        required=True,
        type=str,
        help="Path to sourcode folder",
    )
    mt4py_predict_parser.add_argument(
        "--o",
        required=True,
        type=str,
        help="Path to predicted files folder",
    )
    mt4py_predict_parser.add_argument(
        "--m",
        required=False,
        type=str,
        help="mode",
    )
    mt4py_predict_parser.add_argument(
        "--l", required=False, type=int, help="limit of files to predict"
    )
    mt4py_predict_parser.set_defaults(func=mt4py_predict_projects)

    args = arg_parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
