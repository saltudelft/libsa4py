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
          "classes": [],
          "funcs": [],
          "set": null,
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
- `classes`: Contains the JSON object of processed classes which are described below.
- `funcs`: Contains the JSON object of processed functions in a module, which are described below.
- `set`: Determines to which sets the file belongs to, if `--s` option is provided when running the pipeline. It contains one of the values in `['train', 'valid', 'test']`. The default value is `null`.
- `type_annot_cove`: Type annotations coverage for source code files and the whole project.

## Classes
The following JSON object represents a processed class:

```json
{
  "name": "",
  "variables": {"var_name": "type"},
  "funcs": []
}
```

Description of the fields:
- `name`: The name of the processed class.
- `variables`: Contains class variables' names and their type.
- `funcs`: Contains the JSON object of processed functions in a class, which are described below.

## Functions
The following JSON Object represents a processed function:

```json
{
  "name": "",
  "params": {"param_name":  ""},
  "ret_exprs": [],
  "params_occur": {"param_name":  []},
  "ret_type": "",
  "variables": {"var_name":  ""},
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
- `params`: Contains the parameters of the processed function and their type if available.
- `ret_exprs`: Contains the return expressions of the processed function.
- `ret_type`: Return type of the processed function if available.
- `variables`: Contains variables' names and their type 
- `params_occur`: Contains the parameters and their usages in the body of the processed function.
- `docstring`: Contains docstring of the processed function, which has the following sub-fields:
  - `func`: one-line description of the processed function.
  - `ret`: description of what the processed function returns.
  - `long_descr`: long description of the processed function.