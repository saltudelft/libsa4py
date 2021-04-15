"""
This module contains a naive lenient parser which ignores parse errors by removing problematic tokens
NOTE: USE THIS PARSER IF YOU KNOW WHAT YOU'RE DOING!
"""

from libsa4py.exceptions import ParseTokenError
from typing import Union
from libcst import PartialParserConfig, CSTNode, Module
from libcst._exceptions import get_expected_str, EOFSentinel, ParserSyntaxError
from libcst._parser.base_parser import _token_to_transition, _TokenT, StackNode
from libcst._parser.detect_config import detect_config
from libcst._parser.grammar import validate_grammar, get_grammar
from libcst._parser.python_parser import PythonCSTParser


class LenientPythonParser(PythonCSTParser):
    def __init__(self, *args, **kwargs):
        super(LenientPythonParser, self).__init__(*args, **kwargs)

    def _add_token(self, token: _TokenT) -> None:
        grammar = self._pgen_grammar
        stack = self.stack
        transition = _token_to_transition(grammar, token.type, token.string)

        while True:
            try:
                plan = stack[-1].dfa.transitions[transition]
                break
            except KeyError:
                if stack[-1].dfa.is_final:
                    self._pop()
                else:
                    expected_str = get_expected_str(
                        token, stack[-1].dfa.transitions.keys()
                    )
                    raise ParseTokenError(expected_str, token, token.start_pos[1])

        stack[-1].dfa = plan.next_dfa

        for push in plan.dfa_pushes:
            stack.append(StackNode(push))

        leaf = self.convert_terminal(token)
        stack[-1].nodes.append(leaf)

    def parse(self):
        for token in self.tokens:
            self._add_token(token)

        while True:
            tos = self.stack[-1]
            if not tos.dfa.is_final:
                expected_str = get_expected_str(
                    EOFSentinel.EOF, tos.dfa.transitions.keys()
                )
                raise ParserSyntaxError(
                    f"{expected_str}",
                    lines=self.lines,
                    raw_line=len(self.lines),
                    raw_column=len(self.lines[-1]),
                )

            if len(self.stack) > 1:
                self._pop()
            else:
                return self.convert_nonterminal(tos.nonterminal, tos.nodes)


def _lenient_parse(
    entrypoint: str,
    source: Union[str, bytes],
    config: PartialParserConfig,
    *,
    detect_trailing_newline: bool,
    detect_default_newline: bool,
) -> CSTNode:
    detection_result = detect_config(
        source,
        partial=config,
        detect_trailing_newline=detect_trailing_newline,
        detect_default_newline=detect_default_newline,
    )
    validate_grammar()
    grammar = get_grammar(config.parsed_python_version, config.future_imports)
    parser = LenientPythonParser(
        tokens=detection_result.tokens,
        config=detection_result.config,
        pgen_grammar=grammar,
        start_nonterminal=entrypoint,
    )

    result = parser.parse()
    assert isinstance(result, CSTNode)
    return result


def lenient_parse_module(
    source: Union[str, bytes],
    config: PartialParserConfig = PartialParserConfig(),
) -> Module:

    try:
        result = _lenient_parse(
            "file_input",
            source,
            config,
            detect_trailing_newline=True,
            detect_default_newline=True,
        )
        assert isinstance(result, Module)
        return result
    except ParseTokenError as pse:
        token, idx = pse.get_erroneous_token()
        return lenient_parse_module(source[:idx] + '' + source[idx+1:], config)
