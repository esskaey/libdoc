# -*- coding: utf-8 -*-

from pygments.lexer import RegexLexer
from pygments.token import *
import re

__all__ = ['GCodeLexer']


class GCodeLexer(RegexLexer):
    
    name = 'G-Code'
    aliases = ['gcode']
    filenames = ['*.cnc']

    tokens = {
        'root': [
            (r'^;.*$', Comment),
            (r'[gmtGMT]\d{1,4}\s',Name.Builtin), # M or G commands
            (r'[^gGmM][+-]?\d*[.]?\d+', Keyword),
            (r'\s', Text.Whitespace),
            (r'.*\n', Text),
        ],

        'comment': [
            ('\(', Comment.Multiline, '#push'),
            ('\)', Comment.Multiline, '#pop'),
            ('[^*(]+', Comment.Multiline),
            ('[*(]', Comment.Multiline),
        ],

        'string' : [
            (r"\$(?:[$'LNPRT]|[0-9A-F]{2})", String.Escape),
            (r"[^'$]+", Literal.String),
            (r"'", Literal.String, '#pop'),
        ]        
    }
