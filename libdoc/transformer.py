# -*- coding: utf-8 -*-
"""
    The implementation of the Transformer decorator
"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
import io
import os
import sys
from collections import Mapping, Set

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
        return self.builders.__iter__()

    def __len__(self):
        return self.builders.__len__()

    def __contains__(self, item):
        return self.builders.__contains__(item)


class _TransformerProperty(Mapping):

    def __init__(self, transformer_mapping):
        self.transformers = transformer_mapping

    def __len__(self):
        return self.transformers.__len__()

    def __iter__(self):
        return self.transformers.__iter__()

    def __getitem__(self, key):
        return self.transformers.__getitem__(key)


def format_doc(indent):
    m_builder = max([len(l) for l in _doc.keys()])
    space = ' ' * indent
    return '\n'.join(["{s}{b:<{width}} {d}".format(
        s=space,
        b=builder+':',
        d=_doc[builder],
        width=m_builder+1
    ) for builder in sorted(_doc.keys())])

builders = _BuilderProperty(_builders)
transformers = _TransformerProperty(_transformers)
builder_docs = format_doc


def transformer(builder, doc=''):

    assert isinstance(builder, unicode)
    assert isinstance(doc, unicode)
    assert builder not in _builders, "Format '{}' is already implemented".format(builder)
    _builders.add(builder)
    _doc[builder] = doc

    def decorator(func):
        _transformers[builder] = func
        return func

    return decorator


def create_builder_state(config, builder='html', language=None):
    if builder not in _builders:
        raise BuilderError('The {builder} format is not supported'.format(builder=builder))
    state = os.path.join(config, STATE)
    state_pyc = os.path.splitext(state)[0] + '.pyc'
    try:
        os.remove(state_pyc)
    except OSError:
        pass
    with io.open(state, 'w', encoding='utf-8') as f:
        print('Generate:', state)
        ctx = dict(zip(_builders, [False] * len(_builders)))
        ctx.update({builder: True})
        content = ['# -*- coding: utf-8 -*-',
                   '"""',
                   '    A module, auto generated from libdoc.',
                   '    Import it in your conf.py and you can do some things dependent on its content.',
                   '"""',
                   '',
                   'transformer = "{builder}"',
                   ]
        content.extend(['transformer_{0} = {{ctx[{0}]}}'.format(b) for b in _builders])
        content.append('')
        content.append('language = "{}"'.format(language if language is not None else 'en'))
        content = '\n'.join(content).format(ctx=ctx, builder=builder)
        f.write(content)
    # unload the old state
    mod = os.path.splitext(STATE)[0]
    if mod in sys.modules:
        del sys.modules[mod]
