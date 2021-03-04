# Intro
[![PyPI version](https://badge.fury.io/py/libsa4py.svg)](https://badge.fury.io/py/libsa4py)

`LibSA4Py` is a static analysis library for Python, which extracts type hints and features for training ML-based type inference models.

- [Requirements](#requirements)
- [Quick Installation](#quick-installation)
- [Usage](#usage)
  - [Processing projects](#processing-projects)
  - [Merging projects](#merging-projects)
- [JSON Output](#json-output)

# Requirements

- Python 3.5 or newer (Python 3.8 is recommended)
- MacOS or Linux systems

# Quick Installation

```
git clone https://github.com/saltudelft/libsa4py.git
cd libsa4py && pip install .
```

# Usage
## Processing projects
Given Python repositories, run the following command to process source code files and generate JSON-formatted outputs:
```
libsa4py process --p $REPOS_PATH --o $OUTPUT_PATH --d $DUPLICATE_PATH --j $WORKERS_COUNT --l $LIMIT --c --no-nlp
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

## Merging projects
To merge all the processed JSON-formatted projects into a single dataframe, run the following command:
```
libsa4py merge --o $OUTPUT_PATH
```

Description:
- `--o $OUTPUT_PATH`: Path to the processed projects, used in the previous processing step.

# JSON Output
After processing each project, a JSON-formatted file is produced, which is described [here](https://github.com/saltudelft/light-sa-type-inf/blob/master/JSONOutput.md).