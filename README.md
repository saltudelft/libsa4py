# light-sa-type-inf
A light-weight static analysis-based code representation to do ML-based type inference for Python

# Usage
## Prcossing projects
Given Python repositories, run the following command to process source code files and generate JSON-formatted outputs:
```
libsa4py process --p $REPOS_PATH --o $OUTPUT_PATH --d $DUPLICATE_PATH --j $WORKERS_COUNT --l $LIMIT --c --no-nlp
```

Description:
- `--p $REPOS_PATH`: The path to the Python corpus or dataset.
- `--o $OUTPUT_PATH`: Path to store processed projects.
- `--d $DUPLICATE_PATH`: Path to duplicate files of the given dataset (i.e. jsonl.gz file produced by the [CD4Py](https://github.com/saltudelft/CD4Py) tool). [**Optional**]
- `--j $WORKERS_COUNT`: Number of workers for processing projects. [**Optional**]
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