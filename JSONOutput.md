# JSON Output
After processing each project, a JSON-formatted file is produced, which is described below. 

## Project
```json
{"author/repo": 
  {"src_files": 
    {
      "file_path": 
        {
          "untyped_seq": "",
          "typed_seq": "",
          "imports": [],
          "variables": {"var_name": "type"},
          "mod_var_occur": {"var_name": []},
          "mod_var_ln": {"var_name": [[1,0], [2, 2]]},
          "classes": [],
          "funcs": [],
          "set": null,
          "tc": [false, 5],
          "no_types_annot": {"U":  0, "D": 0, "I": 0},
          "type_annot_cove": 0.0
        }
    },
    "type_annot_cove": 0.0
  }
}
```

Description of the fields:
- `author/repo`: Identifies a project like GitHub, e.g., `Google/Tensorflow`.
- `src_files`: Contains processed source code files of the project.
- `file_path`: Represents an absolute path of the source code file.
- `untyped_seq`: Contains normalized seq2seq representation of the source code file
- `typed_seq`: Contains the type of identifers in `untyped_seq` if present. Otherwise `0` is inserted.
- `imports`: Contains the name of imports in the source code file.
- `variables`: Contains variables' names and their type at the module-level
- `mod_var_occur`: Contains module-level variables and their usages in the processed file.
- `mod_var_ln`: Contains line and column no. info for the start and end of module-level variables.
- `classes`: Contains the JSON object of processed classes which are described below.
- `funcs`: Contains the JSON object of processed functions in a module, which are described below.
- `set`: Determines to which sets the file belongs to, if `--s` option is provided when running the pipeline. It contains one of the values in `['train', 'valid', 'test']`. The default value is `null`.
- `tc`: Whether the processed file is successfully type-checked or not plus no. of type errors if any. **NOTE:** `[false, none]` means that type-checking failed due to the type checker's exceptions.
- `no_types_annot`: Type slots stats for the processed module:
  - `U`: No. of types slots w/o a type annotation.
  - `D`: No of type slots w/ developer-provided annotations.
  - `I`: No. of type slots w/ Pyre-inferred annotations.
- `type_annot_cove`: Type annotations coverage for source code files and the whole project.

> NOTE: For files with no type slots, the value of `type_annot_cove` is 1.0 and the sum of values in `no_types_annot` are 0.

## Classes
The following JSON object represents a processed class:

```json
{
  "name": "",
  "q_name": "",
  "cls_lc": [[5,0], [10, 7]],
  "variables": {"var_name": "type"},
  "cls_var_occur": {"var_name": []},
  "cls_var_ln": {"var_name": [[1,0], [2, 2]]},
  "funcs": []
}
```

Description of the fields:
- `name`: The name of the processed class.
- `q_name`: The qualified name of the processed class.
- `cls_lc`: Contains line and column no. info for the start and end of the class.
- `variables`: Contains class variables' names and their type.
- `cls_var_occur`: Contains class variables' usage inside the class.
- `cls_var_ln`: Contains line and column no. info for the start and end of class variables.
- `funcs`: Contains the JSON object of processed functions in a class, which are described below.

## Functions
The following JSON Object represents a processed function:

```json
{
  "name": "",
  "q_name": "",
  "fn_lc": [[1,0], [2, 2]],
  "params": {"param_name":  ""},
  "ret_exprs": [],
  "params_occur": {"param_name":  []},
  "ret_type": "",
  "variables": {"var_name":  ""},
  "fn_var_occur": {"var_name": []},
  "fn_var_ln": {"var_name": [[1,0], [2, 2]]},
  "params_descr": {"param_name":  ""},
  "docstring": {
    "func": "",
    "ret": "",
    "long_descr": ""
  }
}
```

Description of the fields:
- `name`: The name of the processed function.
- `q_name`: The qualified name of the processed function.
- `fn_lc`: The first list contains the line and column no. of the start of the function. The second list contains the line and column no. of the end of the function.
- `params`: Contains the parameters of the processed function and their type if available.
- `ret_exprs`: Contains the return expressions of the processed function.
- `ret_type`: Return type of the processed function if available.
- `variables`: Contains variables' names and their type
- `fn_var_occur`: Contains the usage of functions' variables in the body of the processed function.
- `fn_var_ln`: Contains line and column no. info for the start and end of functions' local variables.
- `params_occur`: Contains the parameters and their usages in the body of the processed function.
- `docstring`: Contains docstring of the processed function, which has the following sub-fields:
  - `func`: one-line description of the processed function.
  - `ret`: description of what the processed function returns.
  - `long_descr`: long description of the processed function.