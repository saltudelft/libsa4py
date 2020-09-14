"""
In this script, the CST extractor is tested with an example
"""
# TODO: We should write unit tests to test different functionalities of the CST extractor

from libsa4py.extractor_cst import ExtendedExtractorCST
import json

if __name__ == '__main__':

    example_py_src = open("/Users/amir/projects/ML4SE/data/full_data/kennethreitz/requests-html/requests_html.py", 'r').read()
    #example_py_src = open('/Users/amir/projects/ML4SE/data/full_data/snorkel-team/snorkel/setup.py', 'r').read()
    #example_py_src = open('example.py', 'r').read()
    fns = ExtendedExtractorCST().extract(example_py_src)
    print(json.dumps(fns, indent=4))
    with open("libcst_json.json", "w") as json_f:
        json.dump(fns, json_f, indent=4)