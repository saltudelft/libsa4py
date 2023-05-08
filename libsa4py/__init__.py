__version__ = "0.4.0"

# Package constants
DEV_TYPE_ANNOT = 'D'
INF_TYPE_ANNOT = 'I'
UNK_TYPE_ANNOT = 'U'

# Maximum time for type checking in sec.
MAX_TC_TIME = 120

# Python types
PY_TYPING_MOD = {'ABCMeta', 'AbstractSet', 'Any', 'AnyStr', 'AsyncContextManager', 'AsyncGenerator', 'AsyncIterable',
                 'AsyncIterator', 'Awaitable', 'BinaryIO', 'ByteString', 'CT_co', 'Callable', 'ChainMap', 'ClassVar',
                 'Collection', 'Container', 'ContextManager', 'Coroutine', 'Counter', 'DefaultDict', 'Deque', 'Dict',
                 'EXCLUDED_ATTRIBUTES', 'Final', 'ForwardRef', 'FrozenSet', 'Generator', 'Generic', 'Hashable', 'IO',
                 'ItemsView', 'Iterable', 'Iterator', 'KT', 'KeysView', 'List', 'Literal', 'Mapping', 'MappingView',
                 'Match', 'MethodDescriptorType', 'MethodWrapperType', 'MutableMapping', 'MutableSequence',
                 'MutableSet', 'NamedTuple', 'NamedTupleMeta', 'NewType', 'NoReturn', 'Optional', 'OrderedDict',
                 'Pattern', 'Protocol', 'Reversible', 'Sequence', 'Set', 'Sized', 'SupportsAbs', 'SupportsBytes',
                 'SupportsComplex', 'SupportsFloat', 'SupportsIndex', 'SupportsInt', 'SupportsRound', 'T',
                 'TYPE_CHECKING', 'T_co', 'T_contra', 'Text', 'TextIO', 'Tuple', 'Type', 'TypeVar', 'TypedDict',
                 'Union', 'VT', 'VT_co', 'V_co', 'ValuesView', 'WrapperDescriptorType', '_Final', '_GenericAlias',
                 '_Immutable', '_PROTO_WHITELIST', '_ProtocolMeta', '_SPECIAL_NAMES', '_SpecialForm',
                 '_TYPING_INTERNALS', '_TypedDictMeta', '_TypingEllipsis', '_TypingEmpty', '_VariadicGenericAlias'}

PY_COLLECTION_MOD = {'ChainMap', 'Counter', 'OrderedDict', 'UserDict', 'UserList', 'UserString', '_Link',
                     '_OrderedDictItemsView', '_OrderedDictKeysView', '_OrderedDictValuesView', 'defaultdict',
                     'deque', 'namedtuple'} - PY_TYPING_MOD

PY_BUILTINS_MOD = {'ArithmeticError', 'AssertionError', 'AttributeError', 'BaseException', 'BlockingIOError',
                   'BrokenPipeError', 'BufferError', 'BytesWarning', 'ChildProcessError', 'ConnectionAbortedError',
                   'ConnectionError', 'ConnectionRefusedError', 'ConnectionResetError', 'DeprecationWarning',
                   'EOFError', 'Ellipsis', 'EnvironmentError', 'Exception', 'False', 'FileExistsError',
                   'FileNotFoundError', 'FloatingPointError', 'FutureWarning', 'GeneratorExit', 'IOError',
                   'ImportError', 'ImportWarning', 'IndentationError', 'IndexError', 'InterruptedError',
                   'IsADirectoryError', 'KeyError', 'KeyboardInterrupt', 'LookupError', 'MemoryError',
                   'ModuleNotFoundError', 'NameError', 'None', 'NotADirectoryError', 'NotImplemented',
                   'NotImplementedError', 'OSError', 'OverflowError', 'PendingDeprecationWarning', 'PermissionError',
                   'ProcessLookupError', 'RecursionError', 'ReferenceError', 'ResourceWarning', 'RuntimeError',
                   'RuntimeWarning', 'StopAsyncIteration', 'StopIteration', 'SyntaxError', 'SyntaxWarning',
                   'SystemError', 'SystemExit', 'TabError', 'TimeoutError', 'True', 'TypeError', 'UnboundLocalError',
                   'UnicodeDecodeError', 'UnicodeEncodeError', 'UnicodeError', 'UnicodeTranslateError',
                   'UnicodeWarning', 'UserWarning', 'ValueError', 'Warning', 'ZeroDivisionError',
                   'abs', 'all', 'any', 'ascii', 'bin', 'bool', 'breakpoint', 'bytearray', 'bytes', 'callable', 'chr',
                   'classmethod', 'compile', 'complex', 'copyright', 'credits', 'delattr', 'dict', 'dir', 'divmod',
                   'enumerate', 'eval', 'exec', 'exit', 'filter', 'float', 'format', 'frozenset', 'getattr', 'globals',
                   'hasattr', 'hash', 'help', 'hex', 'id', 'input', 'int', 'isinstance', 'issubclass', 'iter', 'len',
                   'license', 'list', 'locals', 'map', 'max', 'memoryview', 'min', 'next', 'object', 'oct', 'open',
                   'ord', 'pow', 'print', 'property', 'quit', 'range', 'repr', 'reversed', 'round', 'set', 'setattr',
                   'slice', 'sorted', 'staticmethod', 'str', 'sum', 'super', 'tuple', 'type', 'vars', 'zip'}
