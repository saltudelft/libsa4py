# Changelog
All notable changes to the [LibSA4Py](https://github.com/saltudelft/libsa4py) tool will be documented in this file. The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Removed
- Removing the unused `input_projects` argument from the `Pipeline` class.

## [0.1.0] - 2021-03-04

### Added
#### Pipeline
- Parallel pipeline to speed up processing a Python dataset using all CPU cores  
- Storing processed Python projects in JSON-formatted files.
- Excluding duplicate files of a dataset from processing.
- Add file set (train/test/validation) to processed project if given.
- Applying standard NLP operations on identifies in a module.
- Excluding cached projects before running the pipeline if specified.
- Throwing `NullProjectException` for projects that have no source code files.

#### AST-based Extractor
- Creating a normalized Seq2Seq representation of a source code file aligned with a sequence of identifiers' type.
- Extracting import names of a module.
- Extracting the name of global variables in a module with their type annotations (if present).
- Calculating type annotation coverage for the whole project and its source code files.
- Extracting the name of classes in a module.
- Extracting the name of class variables and their type annotation (if present).
- Extracting the name of functions in a module or in a class.
- Extracting the name of functions' parameters and their type annotations (if present).
- Extracting return expressions in functions.
- Extracting the occurrence of a function's parameters in the function's body.
- Extracting the return type of functions (if present).
- Extracting docstring for functions' parameters and their return type.
- Extracting short and long descriptions of functions in their docstring.

#### AST-based Transformers
- Adding space around source code tokens for better tokenization.
- Removing comment and docstring from source code for its normalized Seq2Seq representation.
- Removing string literals from source code for its normalized Seq2Seq representation.
- Removing numeric literals from source code for its normalized Seq2Seq representation.
- Removing type annotations from source code for its normalized Seq2Seq representation.
- Propagating the type of functions' parameters in the function body and module-level constants.

### Fixed
- A special case where uninitialized variables with types caused exceptions.
- A case where variables in a tuple couldn't be extracted in multiple assignments.
- Handling nested tuples in multiple assignments for extracting var names.
- A case where a type-annotated class attribute is not initialized for removing its type.