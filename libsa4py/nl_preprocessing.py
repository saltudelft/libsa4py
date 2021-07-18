from __future__ import unicode_literals
from functools import reduce
from typing import Optional, Tuple, List, Pattern, Match

import docstring_parser
import re
import functools
import nltk

NLTK_STOP_WORDS = nltk.corpus.stopwords.words('english')
LEMMATIZER = nltk.WordNetLemmatizer()
LEMMATIZER.lemmatize("warm up")  # Loads lemmatizer corpus

# nltk.download('averaged_perceptron_tagger')
# nltk.download('stopwords')
# nltk.download('wordnet')

# Precompile often used regex
first_cap_regex = re.compile('(.)([A-Z][a-z]+)')
all_cap_regex = re.compile('([a-z0-9])([A-Z])')


class NLPreprocessor:

    @functools.lru_cache(maxsize=2048)
    def process_sentence(self, sentence: str) -> Optional[str]:
        """
        Process a natural language sentence
        """

        if sentence is None:
            return None

        pipeline = [
            SentenceProcessor.replace_digits_with_space,
            SentenceProcessor.remove_punctuation_and_linebreaks,
            SentenceProcessor.tokenize,
            SentenceProcessor.lemmatize,
            SentenceProcessor.remove_stop_words
        ]

        return reduce(lambda s, action: action(s), pipeline, sentence)

    @functools.lru_cache(maxsize=2048)
    def process_identifier(self, sentence: str) -> str:
        """
        Process a sentence mainly consisting of identifiers

        Similar to process_sentence, but does not remove stop words.
        """
        pipeline = [
            SentenceProcessor.replace_digits_with_space,
            SentenceProcessor.remove_punctuation_and_linebreaks,
            SentenceProcessor.tokenize,
            SentenceProcessor.lemmatize
        ]

        return reduce(lambda s, action: action(s), pipeline, sentence)


class SentenceProcessor:
    """
    A collection of static functions to process a natural language sentence

    Roughly based on https://github.com/sola-da/NL2Type/blob/master/scripts/preprocess_raw_data.py
    """

    @staticmethod
    def process_sentence(sentence: str) -> Optional[str]:
        """
        Process a natural language sentence
        """

        if sentence is None:
            return None

        pipeline = [
            SentenceProcessor.replace_digits_with_space,
            SentenceProcessor.remove_punctuation_and_linebreaks,
            SentenceProcessor.tokenize,
            SentenceProcessor.lemmatize,
            SentenceProcessor.remove_stop_words
        ]

        return reduce(lambda s, action: action(s), pipeline, sentence)

    @staticmethod
    def replace_digits_with_space(sentence: str) -> str:
        """
        Replaces digits with a space
        """
        return re.sub('[0-9]+', ' ', sentence)

    @staticmethod
    def remove_punctuation_and_linebreaks(sentence: str) -> str:
        """
        Removes and replaces non-textual elements

        Removes whitespace and all punctuations. Question marks and full stops are replaced with
        a space. Full stops that are not followed by a space are also replaced with a space, e.g. object.property ->
        object property.
        """
        return re.sub('[^A-Za-z0-9 ]+', ' ', sentence) \
            .replace('\n', '') \
            .replace('\r', '')

    @staticmethod
    def tokenize(sentence: str) -> str:
        """
        Tokenize camel case and snake case in a sentence and convert the sentence to lower case
        """
        sentence = sentence.replace("_", " ")
        sentence = SentenceProcessor.convert_camelcase(sentence)

        return sentence.lower()

    @staticmethod
    def lemmatize(sentence: str) -> str:
        """
        Lemmatize a sentence (e.g. running -> run)
        """
        words = [word for word in sentence.split(' ') if word != '']

        lemmatized = []
        for token, tag in nltk.pos_tag(words):
            word_pos = SentenceProcessor.get_wordnet_pos(tag)
            try:
                if word_pos != '':
                    lemmatized.append(LEMMATIZER.lemmatize(token, pos=word_pos))
                else:
                    lemmatized.append(LEMMATIZER.lemmatize(token))
            except UnicodeDecodeError:
                print(f'Lemmatization failed for {token}, tag: {tag}, word pos: {word_pos}')

        return ' '.join(lemmatized)

    @staticmethod
    def remove_stop_words(sentence: str) -> str:
        """
        Remove stop words from a sentence
        """
        return ' '.join([word for word in sentence.split(' ') if word not in NLTK_STOP_WORDS])

    @staticmethod
    def get_wordnet_pos(treebank_tag: str) -> str:
        """
        Get the WordNet part-of-speech constant for the treebank tag
        """
        if treebank_tag.startswith('J'):
            return nltk.corpus.wordnet.ADJ
        elif treebank_tag.startswith('V'):
            return nltk.corpus.wordnet.VERB
        elif treebank_tag.startswith('N'):
            return nltk.corpus.wordnet.NOUN
        elif treebank_tag.startswith('R'):
            return nltk.corpus.wordnet.ADV
        else:
            return ''

    @staticmethod
    def convert_camelcase(sentence: str) -> str:
        """
        Convert `camelCase` to `camel case`.
        """
        words = [all_cap_regex.sub(r'\1 \2', first_cap_regex.sub(r'\1 \2', word)) for word in sentence.split(" ")]

        return ' '.join(words)


def extract_docstring_descriptions(docstring: str) -> Tuple[dict, dict]:
    """Extract the return description from the docstring"""
    try:
        parsed_docstring: docstring_parser.parser.Docstring = docstring_parser.parse(docstring)

        fn_docstring = {"func": parsed_docstring.short_description, "ret": None,
                        "long_descr": None}
        params_descr = {}

        if parsed_docstring.returns is not None:
            fn_docstring["ret"] = parsed_docstring.returns.description

        if parsed_docstring.long_description is not None:
            fn_docstring['long_descr'] = parsed_docstring.long_description

        for param in parsed_docstring.params:
            params_descr[param.arg_name] = param.description

        return fn_docstring, params_descr
    except Exception:
        return {"func": None, "ret": None, "long_descr": None}, {}


def __check_func_docstring(self, docstring: str) -> Optional[str]:
    """Check the docstring if it has a valid structure for parsing and returns a valid docstring."""
    dash_line_matcher: Pattern[str] = re.compile("\s*--+")
    param_keywords: List[str] = ["Parameters", "Params", "Arguments", "Args"]
    return_keywords: List[str] = ["Returns", "Return"]
    break_keywords: List[str] = ["See Also", "Examples"]

    convert_docstring: bool = False
    add_indent: bool = False
    add_double_colon: bool = False
    active_keyword: bool = False
    end_docstring: bool = False

    preparsed_docstring: str = ""
    lines: List[str] = docstring.split("\n")
    for line in lines:
        result: Optional[Match] = re.match(dash_line_matcher, line)
        if result is not None:
            preparsed_docstring = preparsed_docstring[:-1] + ":" + "\n"
            convert_docstring = True
        else:
            for keyword in param_keywords:
                if keyword in line:
                    add_indent = True
                    active_keyword = True
                    break
            if not active_keyword:
                for keyword in return_keywords:
                    if keyword in line:
                        add_indent = True
                        add_double_colon = True
                        active_keyword = True
                        break
            if not add_double_colon:
                for keyword in break_keywords:
                    if keyword in line:
                        end_docstring = True
                        break
            if end_docstring:
                break
            if active_keyword:
                preparsed_docstring += line + "\n"
                active_keyword = False
            elif add_double_colon:
                preparsed_docstring += "\t" + line + ":\n"
                add_double_colon = False
            elif add_indent:
                line_parts = line.split(":")
                if len(line_parts) > 1:
                    preparsed_docstring += "\t" + line_parts[0] + "(" + line_parts[1].replace(" ", "") + "):\n"
                else:
                    preparsed_docstring += "\t" + line + "\n"
            else:
                preparsed_docstring += line + "\n"

    if convert_docstring:
        return preparsed_docstring
    else:
        return


def normalize_module_code(m_code: str) -> str:
    # New lines
    m_code = re.compile(r"\n").sub(r" [EOL] ", m_code)
    # white spaces
    m_code = re.compile(r"[ \t\n]+").sub(" ", m_code)

    # Replace comments, docstrings, numeric literals and string literals with special tokens
    special_tks = {"#[comment]": "[comment]", "\"\"\"[docstring]\"\"\"": "[docstring]", "\"[string]\"": "[string]",
                   "\"[number]\"": "[number]"}
    regex = re.compile("(%s)" % "|".join(map(re.escape, special_tks.keys())))
    m_code = regex.sub(lambda mo: special_tks[mo.string[mo.start():mo.end()]], m_code)

    return m_code.strip()
