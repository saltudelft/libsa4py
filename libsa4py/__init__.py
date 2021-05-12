__version__ = "0.1.0"

# Package constants
DEV_TYPE_ANNOT = 'D'
INF_TYPE_ANNOT = 'I'
UNK_TYPE_ANNOT = 'U'

PY_TYPING_MOD = {'AbstractSet', 'Any', 'AnyStr', 'AsyncContextManager', 'AsyncGenerator', 'AsyncIterable',
                 'AsyncIterator', 'Awaitable', 'BinaryIO', 'ByteString', 'CT_co', 'Callable', 'ChainMap', 'ClassVar',
                 'Collection', 'Container', 'ContextManager', 'Coroutine', 'Counter', 'DefaultDict', 'Deque', 'Dict',
                 'ForwardRef', 'FrozenSet', 'Generator', 'Generic', 'Hashable', 'IO', 'ItemsView', 'Iterable',
                 'Iterator', 'KT', 'KeysView', 'List', 'Mapping', 'MappingView', 'Match', 'MethodDescriptorType',
                 'MethodWrapperType', 'MutableMapping', 'MutableSequence', 'MutableSet', 'NamedTuple', 'NamedTupleMeta',
                 'NewType', 'NoReturn', 'Optional', 'OrderedDict', 'Pattern', 'Reversible', 'Sequence', 'Set', 'Sized',
                 'SupportsAbs', 'SupportsBytes', 'SupportsComplex', 'SupportsFloat', 'SupportsInt', 'SupportsRound',
                 'TYPE_CHECKING', 'T_co', 'T_contra', 'Text', 'TextIO', 'Tuple', 'Type', 'TypeVar', 'Union', 'VT',
                 'VT_co', 'V_co', 'ValuesView', 'WrapperDescriptorType', '_Final', '_GenericAlias', '_Immutable',
                 '_Protocol', '_ProtocolMeta', '_SpecialForm', '_TypingEllipsis', '_TypingEmpty',
                 '_VariadicGenericAlias'}

PY_COLLECTION_MOD = {'ChainMap', 'Counter', 'OrderedDict', 'UserDict', 'UserList', 'UserString', '_Link',
                     '_OrderedDictItemsView', '_OrderedDictKeysView', '_OrderedDictValuesView', 'defaultdict',
                     'deque', 'namedtuple'} - PY_TYPING_MOD



