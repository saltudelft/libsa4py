"""
This module contains a set of helper functions to merge processed projects into a Dataframe or a single JSON
"""

from libsa4py.utils import list_files, save_json
from libsa4py.nl_preprocessing import NLPreprocessor
from tqdm import tqdm
from os.path import join
import json
import numpy as np
import pandas as pd

NLP_P = NLPreprocessor()


def merge_jsons_to_dict(json_files: list, limit: int = None) -> dict:
    """
    Merges all the JSON files of projects into a dictionary
    """

    if limit is not None:
        json_files = json_files[:limit]

    all_projects_dict = {'projects': {}}
    for f in tqdm(json_files, total=len(json_files), desc="Merging JSONs"):
        with open(f, 'r') as json_f:
            try:
                d = json.load(json_f)
                all_projects_dict['projects'][list(d.keys())[0]] = d[list(d.keys())[0]]
            except json.JSONDecodeError as err:
                print("Could not parse file: ", f)

    return all_projects_dict


def extract_fns(projects: dict) -> list:
    """
    Extracts all the functions from the projects' dictionary in a format that can be converted to a dataframe
    """

    fns = []
    for p in tqdm(list(projects['projects'].keys()), total=len(projects['projects'].keys()), desc="Extracting all functions"):
        p_fns = {'author': '', 'repo': '', 'files': {}}
        p_fns['author'], p_fns['repo'] = p.split("/")
        for f in projects['projects'][p]['src_files'].keys():
            p_fns['files'][f] = {}
            p_fns['files'][f]['set'] = projects['projects'][p]['src_files'][f]['set']
            p_fns['files'][f]['imports'] = [NLP_P.process_identifier(i) for i in
                                            projects['projects'][p]['src_files'][f]['imports']]
            cls_fns = [f for c in projects['projects'][p]['src_files'][f]['classes'] for f in c['funcs']]
            f_fns = projects['projects'][p]['src_files'][f]['funcs']
            p_fns['files'][f]['fns'] = f_fns + cls_fns
        for f in p_fns['files']:
            for fn in p_fns['files'][f]['fns']:
                fns.append([p_fns['author'], p_fns['repo'], f, fn['name'], p_fns['files'][f]['set'],
                            any(t for t in list(fn['params'].values())) or fn['ret_type'] != '',
                            fn['docstring']['long_descr'] if fn['docstring']['long_descr'] is not None else np.NaN,
                            fn['docstring']['func'] if fn['docstring']['func'] is not None else np.NaN,
                            str(list(fn['params'].keys())), str(list(fn['params'].values())),
                            str(list(fn['params_descr'].values())),
                            fn['ret_type'] if fn['ret_type'] != '' else np.NaN,
                            str(fn['ret_exprs']), str(list(fn['params_occur'].values())),
                            fn['docstring']['ret'] if fn['docstring']['ret'] is not None else np.NaN,
                            list(fn['variables'].keys()), list(fn['variables'].values()),
                            str(p_fns['files'][f]['imports']), len(list(fn['params'].keys())),
                            len([t for t in list(fn['params'].values()) if t != ''])])

    return fns


def extract_vars(projects: dict) -> list:
    """
    Extracts all the variables from the projects' dictionary in a format that can be converted to a dataframe
    """

    vars = []
    for p in tqdm(list(projects['projects'].keys()), total=len(projects['projects'].keys()), desc="Extracting all variables"):
        p_vars = {'author': '', 'repo': ''}
        p_vars['author'], p_vars['repo'] = p.split("/")
        for f in projects['projects'][p]['src_files'].keys():
            # module vars
            m_v_occur = list(projects['projects'][p]['src_files'][f]['mod_var_occur'].values())
            for i, m_v in enumerate(projects['projects'][p]['src_files'][f]['variables'].keys()):
                vars.append([p_vars['author'], p_vars['repo'], f, projects['projects'][p]['src_files'][f]['set'], 
                             None, None, m_v, projects['projects'][p]['src_files'][f]['variables'][m_v], m_v_occur[i],
                             str(projects['projects'][p]['src_files'][f]['imports'])])

            for c in projects['projects'][p]['src_files'][f]['classes']:
                # class vars
                c_v_occur = list(c['cls_var_occur'].values())
                for i, c_v in enumerate(c['variables'].keys()):
                    vars.append([p_vars['author'], p_vars['repo'], f, projects['projects'][p]['src_files'][f]['set'], 
                                 c['name'], None, c_v, c['variables'][c_v], c_v_occur[i],
                                 str(projects['projects'][p]['src_files'][f]['imports'])])
                
                for c_fn in c['funcs']:
                    # class functions vars
                    c_fn_occur = list(c_fn['fn_var_occur'].values())
                    for i, fn_v in enumerate(c_fn['variables'].keys()):
                        vars.append([p_vars['author'], p_vars['repo'], f, projects['projects'][p]['src_files'][f]['set'], 
                                     c['name'], c_fn['name'], fn_v, c_fn['variables'][fn_v], c_fn_occur[i],
                                     str(projects['projects'][p]['src_files'][f]['imports'])])

            for fn in projects['projects'][p]['src_files'][f]['funcs']:
                # module functions vars
                fn_v_occur = list(fn['fn_var_occur'].values())
                for i, fn_v in enumerate(fn['variables'].keys()):
                    vars.append([p_vars['author'], p_vars['repo'], f, projects['projects'][p]['src_files'][f]['set'], 
                                 None, fn['name'], fn_v, fn['variables'][fn_v], fn_v_occur[i],
                                 str(projects['projects'][p]['src_files'][f]['imports'])])
    return vars

def create_dataframe_vars(output_path: str, merged_jsons: dict):
    """
    Creates a single dataframe that contains all the extracted variables and type hints for further processing
    """

    vars = extract_vars(merged_jsons)
    df_vars = pd.DataFrame(vars, columns=['author', 'repo', 'file', 'set', 'cls_name', 'fn_name', 'var_name', 'var_type',
                                          'var_occur', 'aval_types'])
    df_vars.to_csv(join(output_path, 'all_vars.csv'), index=False)

def create_dataframe_fns(output_path: str, merged_jsons: dict):
    """
    Creates a single dataframe that contains all the extracted functions and type hints for further processing
    """

    fns = extract_fns(merged_jsons)
    df_fns = pd.DataFrame(fns, columns=['author', 'repo', 'file', 'name', 'set', 'has_type', 'docstring', 'func_descr',
                                        'arg_names', 'arg_types', 'arg_descrs', 'return_type', 'return_expr',
                                        'args_occur', 'return_descr', 'variables', 'variables_types', 'aval_types',
                                        'arg_names_len', 'arg_types_len'])
    df_fns.to_csv(join(output_path, 'all_fns.csv'), index=False)


def merge_projects(args):
    """
    Saves merged projects into a single JSON file and a Dataframe
    """
    merged_jsons = merge_jsons_to_dict(list_files(join(args.o, 'processed_projects'), ".json"), args.l)
    save_json(join(args.o, 'merged_%s_projects.json' % (str(args.l) if args.l is not None else 'all')), merged_jsons)
    create_dataframe_fns(args.o, merged_jsons)
