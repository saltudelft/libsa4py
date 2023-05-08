# Changelog
All notable changes to the [LibSA4Py](https://github.com/saltudelft/libsa4py) tool will be documented in this file. The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2023-05-08
### Added
- Adds the `CountParametricTypeDepth` visitor to count the depth of parametric types.
### Fixed
- Fixed an issue where type annotations for local variables with the same name in methods were not applied (`TypeAlpplier`).

## [0.3.0] - 2022-02-17
### Added
- Adding the `--tc` CLI arg for the `process` command to type-check source files in Python projects using mypy.
- Supporting qualified names for classes by adding the `q_name` field to the JSON output.
- Adding line and column no. info for the start and end of:
  - Functions definitions
  - Class definitions
  - Module-level variables
  - Class variables
  - Functions' local variables
- Improved the performance of the NLP preprocessing quite significantly (~10x).
- Adds a CST visitor (`TypeAnnotationCounter`) for counting the total number of type annotations in source files.

### Fixed
- When applying types to functions' parameters, parameters with the default value of lambdas causes an exception for matching functions' signature.

### Changed
- Python 3.6 is no longer supported.

## [0.2.0] - 2021-06-02
### Added
- Integrated [pyre](https://pyre-check.org/) into the pipeline for inferring the types of variables in source code files of given projects
- Extracting the usage of module constants, class variables, and local variables across a source code file (Contextual hint)
- Adding extensive units tests for testing various features and components of LibSA4Py.
- Minor improvement to the `SpaceAdder` code transformer for handling some rare edge cases.
- The `--l` CLI arg for `merge` option to process a specified number of projects.
- Adding a CST transformer to reduce the depth of parametric types.
- Extracting type annotations with a qualified name from source code files.
- Adding `apply` command to apply inferred type annotations to source code files.
- Adding a qualified name for functions in the JSON field `q_name`.
- Adding line and column no. for the start and end of functions in the JSON field `fn_lc`.

### Fixed
- Malformed output sequences containing string literal type, i.e., `Literal['Blah \n blah']`.
- Malformed output sequence for the Equal operator (i.e. `==`) in comparisons
- Extracting self variables in multi assignments expressions like `self.x,self.y=1,2`.
- Replacing imaginary numbers with the `[numeric]` token.

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