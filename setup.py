from setuptools import setup
from os import path
from libsa4py import __version__

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='libsa4py',
    version=__version__,
    description='LibSA4Py: Light-weight static analysis for extracting type hints and features',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/saltudelft/libsa4py',
    author='Amir M. Mir (TU Delft)',
    author_email='mir-am@hotmail.com',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Environment :: Console',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Operating System :: Unix',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    keywords='libsa4py static analysis features type hints type inference machine learning python pipeline light-weight',
    packages=['libsa4py'],
    python_requries='>=3.5',
    install_requires=['libcst', 'numpy', 'pandas', 'nltk', 'joblib', 'tqdm', 'docstring_parser', 'dpu_utils',
                      'pyre-check', 'toml', 'mypy'],
    entry_points={
        'console_scripts': [
            'libsa4py = libsa4py.__main__:main',
        ],
    }
)
