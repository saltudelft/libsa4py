# Intro
[![PyPI version](https://badge.fury.io/py/libsa4py.svg)](https://badge.fury.io/py/libsa4py) 
![GH Workflow](https://github.com/saltudelft/libsa4py/actions/workflows/libsa4py_test.yaml/badge.svg)

`LibSA4Py` is a static analysis library for Python, which extracts type hints and features for training ML-based type inference models.

- [Intro](#intro)
- [Requirements](#requirements)
- [Quick Installation](#quick-installation)
- [Usage Libsa4Py](#usage-libsa4py)
  - [Processing projects](#processing-projects)
  - [Merging projects](#merging-projects)
  - [Applying types](#applying-types)
- [MyType4Py](#mytype4py)
  - [Description:](#description)
  - [1. Predict:](#1-predict)
- [JSON Output](#json-output)

# Requirements

- Python 3.7 or newer (Python 3.8 is recommended)
- [Watchman](https://facebook.github.io/watchman/) (for running [pyre](https://pyre-check.org/)) [**Optional**]
- MacOS or Linux systems

# Quick Installation

```
git clone https://github.com/saltudelft/libsa4py.git
cd libsa4py && pip install .
```

# Usage Libsa4Py
## Processing projects
Given Python repositories, run the following command to process source code files and generate JSON-formatted outputs:
```
libsa4py process --p $REPOS_PATH --o $OUTPUT_PATH --d $DUPLICATE_PATH --j $WORKERS_COUNT --l $LIMIT --c --no-nlp --pyre
```

Description:
- `--p $REPOS_PATH`: The path to the Python corpus or dataset.
- `--o $OUTPUT_PATH`: Path to store processed projects.
- `--d $DUPLICATE_PATH`: Path to duplicate files of the given dataset (i.e. jsonl.gz file produced by the [CD4Py](https://github.com/saltudelft/CD4Py) tool). [**Optional**]
- `--s`: Path to the CSV file for splitting the given dataset. [**Optional**]
- `--j $WORKERS_COUNT`: Number of workers for processing projects. [**Optional**, default=no. of available CPU cores]
- `--l $LIMIT`: Number of projects to be processed. [**Optional**]
- `--c`: Whether to ignore processed projects. [**Optional**, default=False]
- `--no-nlp`: Whether to apply standard NLP techniques to extracted identifiers. [**Optional**, default=True]
- `--pyre`: Whether to run `pyre` to infer the types of variables for given projects. [**Optional**, default=False]
- `--tc`: Whether to type-check type annotations in projects. [**Optional**, default=False]

## Merging projects
To merge all the processed JSON-formatted projects into a single dataframe, run the following command:
```
libsa4py merge --o $OUTPUT_PATH --l $LIMIT
```

Description:
- `--o $OUTPUT_PATH`: Path to the processed projects, used in the previous processing step.
- `--l $LIMIT`: Number of projects to be merged. [**Optional**]

## Applying types
To apply Pyre's inferred types to projects, run the following command:
```
libsa4py apply --p $REPOS_PATH --o $OUTPUT_PATH
```

Description:
- `--p $REPOS_PATH`: The path to the Python corpus or dataset.
- `--o $OUTPUT_PATH`: Path to the processed projects, used in the previous processing step.

# MyType4Py
## Description:
MyType4Py is an extension on LibSA4Py that uses Mypy to test Type4Py's type-correctness. This Pipeline has 4 Main steps: 
1. **Predict:** Uses Type4Py's API to predict types for sourcecode files in a folder.
2. **APM (Apply Prediction Method):** Applies a prediction method (more on that below) to the given prediction files. Type4Py gives not only one prediction, it gives multiple with different levels of confidence scores. One greedy prediction method could be to only pick the prediction with the highest confidence score.
3. **ATS (Apply Types to Sourcecode):** Inspired by the normal LibSA4Py apply method but with different inputs and outputs that match MyType4Py's second and fourth step. 
4. **ATC (Apply Type check):** Uses Mypy to check Type4Py's applied types. 

## 1. Predict:
Given source files all in the same folder, uses Type4Py to predict types via the REST API. 

```
libsa4py mt4py_predict --s $REPOS_PATH --o $OUTPUT_PATH --l $LIMIT
```
Description:
- `--s $REPOS_PATH`: The Path to the folder containing python source files for prediction
- `--o $OUTPUT_PATH`: The Path to the folder that contains all the output predictions in json files. 
- `--l $LIMIT`: Number of projects to be predicted. [**Optional**]

Additional Info: 
First time running the $OUTPUT_PATH folder should be made. 
The predict method will make a new file called "existing_predictions.txt". This makes it possible to continue where you left off with predicting if a crash happens. If you want to rerun the whole prediction you should delete this file. 

# JSON Output
After processing each project, a JSON-formatted file is produced, which is described [here](https://github.com/saltudelft/light-sa-type-inf/blob/master/JSONOutput.md).