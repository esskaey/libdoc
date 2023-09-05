# -*- coding: utf-8 -*-
"""
    The implementation of the Transformer decorator
"""
import io
import os
import sys
from collections.abc import Mapping, Set

from .exceptions import BuilderError

__all__ = ["transformer", "builders", "transformers", "STATE", "create_builder_state", "builder_docs"]

STATE = 'libdoc_builder.py'  #: The name of the builder state file

_builders = set()
_transformers = {}
_doc = {}


class _BuilderProperty(Set):

    def __init__(self, builder_sequence):
        self.builders = builder_sequence

    def __iter__(self):
        return iter(self.builders)

    def __len__(self):
        return len(self.builders)

    def __contains__(self, item):
        return item in self.builders


class _TransformerProperty(Mapping):

    def __init__(self, transformer_mapping):
        self.transformers = transformer_mapping

    def __len__(self):
        return len(self.transformers)

    def __iter__(self):
        return iter(self.transformers)

    def __getitem__(self, key):
        return self.transformers[key]


def format_doc(indent):
    m_builder = max(len(l) for l in _doc.keys())
    space = ' ' * indent
    return '\n'.join([f"{space}{builder:<{m_builder + 1}} {_doc[builder]}" for builder in sorted(_doc.keys())])

builders = _BuilderProperty(_builders)
transformers = _TransformerProperty(_transformers)
builder_docs = format_doc


def transformer(builder, doc=''):
    assert isinstance(builder, str)
    assert isinstance(doc, str)
    assert builder not in _builders, f"Format '{builder}' is already implemented"
    _builders.add(builder)
    _doc[builder] = doc

    def decorator(func):
        _transformers[builder] = func
        return func

    return decorator


def create_builder_state(config, builder='html', language=None):
    if builder not in _builders:
        raise BuilderError(f'The {builder} format is not supported')
    state = os.path.join(config, STATE)
    state_pyc = os.path.splitext(state)[0] + '.pyc'
    try:
        os.remove(state_pyc)
    except FileNotFoundError:
        pass

    with io.open(state, 'w', encoding='utf-8') as f:
        print('Generate:', state)
        ctx = {b: False for b in _builders}
        ctx[builder] = True
        content = [
            '# -*- coding: utf-8 -*-',
            '"""',
            '    A module, auto generated from libdoc.',
            '    Import it in your conf.py and you can do some things dependent on its content.',
            '"""',
            '',
            f'transformer = "{builder}"'
        ]
        content.extend([f'transformer_{b} = {ctx[b]}' for b in _builders])
        content.append('')
        content.append(f'language = "{language if language is not None else "en"}"')
        f.write('\n'.join(content))
    
    # unload the old state
    mod = os.path.splitext(STATE)[0]
    if mod in sys.modules:
        del sys.modules[mod]
