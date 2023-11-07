# -*- coding: utf-8 -*-

from pygments.lexer import RegexLexer
from pygments.token import Text,Comment,Literal,String,Number,Name,Punctuation,Keyword
import re

__all__ = ['CDSLexer']

class CDSLexer(RegexLexer):
    """
    For `CODESYS <http://www.codesys.com>`_ flavored Structured Text.
    A formal language for industrial automation specified by IEC 61131-3.
    """
    
    name = 'CODESYS'
    aliases = ['codesys']
    filenames = ['*.cds']
    mimetypes = ['text/x-codesys']

    cdsWord = 'BYTE|(?:D|L)?WORD'
    cdsInt =  'U?(?:S|D|L)?INT'
    cdsNumber = '|'.join([cdsWord, cdsInt])
    cdsReal = '(?:L)?REAL'
    cdsAny = 'ANY(?:_(?:BIT|DATE|INT|NUM|REAL))?'

    cdsNumericType = '|'.join([cdsReal, cdsNumber, '__(?:XWORD|UXINT|XINT)'])
    cdsSafetyType = 'SAFE(?:%s)' % '|'.join(['BOOL', 'TIME', cdsNumber])
    cdsDataType = '|'.join(['__LAZY|BOOL|BIT|W?STRING|TIME(?:_OF_DAY)?',
                            'LTIME|DATE(?:_AND_TIME)?|DT|TOD',
                            cdsNumericType, cdsSafetyType, cdsAny
                           ])

    cdsConvert = '(?P<t>{0})_TO_(?!(?P=t)\b)(?:{0})'
    cdsFloat = r'[+-]?(?:(?:{0})#)?\d+(?:\.\d+)(?:[eE][+-]?\d{{1,3}})?'
    cdsHex = r'[+-]?(?:(?:{0})#)?(?:16#)[0-9A-F][0-9A-F_]*'
    cdsOct = r'[+-]?(?:(?:{0})#)?(?:8#)[0-7][0-7_]*'
    cdsBin = r'[+-]?(?:(?:{0})#)?(?:2#)[01][01_]*'
    cdsDec = r'[+-]?(?:(?:{0})#)?[0-9][0-9_]*'
    cdsDate = r'(?:DATE|D)#\d{4}(?:-\d{2}){2}'
    cdsDateAndTime = (r'(?:DATE_AND_TIME|DT)#\d{4}'
                      r'(?:-\d{2}){3}:\d{2}(?:[:]\d{2}(?:[.]\d+)?)?')
    cdsTime = (r'(?:TIME|T)#(?:\d+(?:[.]\d+)?D)?(?:\d+(?:[.]\d+)?H)?'
               r'(?:\d+(?:[.]\d+)?M(?!S))?(?:\d+(?:[.]\d+)?S)?'
               r'(?:\d+(?:[.]\d+)?MS)?')
    cdsLTime = (r'LTIME#(?:\d+(?:[.]\d+)?D)?(?:\d+(?:[.]\d+)?H)?'
                r'(?:\d+(?:[.]\d+)?M(?!S))?(?:\d+(?:[.]\d+)?S)?'
                r'(?:\d+(?:[.]\d+)?MS)?(?:\d+(?:[.]\d+)?US)?'
                r'(?:\d+(?:[.]\d+)?NS)?')
    cdsTimeOfDay = r'(?:TIME_OF_DAY|TOD)#\d{2}:\d{2}(?:[:]\d{2}(?:[.]\d+)?)?'
    
    flags = re.IGNORECASE
    tokens = {
        'root': [
            (r'\s+', Text),
            (r'\(\*', Comment.Multiline, 'comment'),
            (r'///.*?\n', Comment.Special),
            (r'//.*?\n', Comment.Single),
            (r'\[(?:.|\n)*?\]', Literal),
            (r'{(?:.|\n)*?}', Comment.Preproc),
            (r'(?:REF=|S=|R=|:=|\*\*)', Punctuation),
            (r"'", Literal.String, 'string'), # STRING
            (r'"', Literal.String, 'wstring'), # WSTRING
            (cdsFloat.format(cdsReal), Number.Float),
            (cdsHex.format(cdsNumber), Number.Hex),
            (cdsOct.format(cdsNumber), Number.Oct),
            ('|'.join((
                       r'BOOL#[01]',
                       cdsBin.format(cdsNumber), cdsDec.format(cdsNumber),
                      )), Number.Integer
            ),
            (cdsDate, Literal.Date),
            ('|'.join((
                       cdsDateAndTime, cdsTime, cdsLTime, cdsTimeOfDay,
                       r'%(?:I|M|Q)(:?X|B|W|D|L)?\d+(?:[.]\d+)*', # Address
                     )), Literal
            ),
            (cdsConvert.format(cdsDataType), Name.Builtin),
            (r'REFERENCE_TO_POINTER', Name.Builtin),
            (r'\b(%s)\b' % cdsDataType, Keyword.Type),
            (r'\b__SYSTEM([.][A-Z_][A-Z0-9_.]*)\b', Name.Builtin),
            (r'\b(__(COPY|RELOC|CRC|MAXOFFSET|LOCALOFFSET|TYPEOF|VARINFO|INIT|CAST)|'
             r'PUBLIC|PRIVATE|PROTECTED|INTERNAL|FINAL|'
             r'__(ISVALIDREF|FCALL|PROPERTYINFO|ADRINST|REFADR|MEMSET|'
             r'QUERY(INTERFACE|POINTER)|NEW|DELETE|WAIT|BITOFFSET)|'
             r'VAR_(ACCESS|CONFIG|EXTERNAL|GLOBAL|INPUT|IN_OUT|OUTPUT|TEMP|STAT)|'
             r'(END_)?(CASE|FOR|IF|REPEAT|STRUCT|UNION|TYPE|VAR|WHILE)|MOVE|'
             r'MODULE|IMPLEMENTED_BY|(END_)?SEC|IMPORTS|'
             r'INTERFACE|EXIT|CONTINUE|FROM|FUNCTION(_BLOCK)?|POINTER|'
             r'REFERENCE|PROGRAM|PARAMS|PERSISTENT|THEN|RETAIN|RETURN|UNTIL|'
             r'WITH|EXTENDS|IMPLEMENTS|METHOD|PROPERTY|THIS|SUPER|'
             r'ARRAY|CONSTANT|DO|ELSE|ELSIF|AND|OR|NOT|XOR|MOD|TEST_AND_SET|'
             r'BITADR|ADR|INDEXOF|SIZEOF|INI|ABS|LIMIT|MIN|MAX|TRUNC(_INT)?|'
             r'MUX|SEL|ROL|ROR|SHL|SHR|EXP(T)?|SQRT|LN|LOG|SIN|COS|TAN|ASIN|'
             r'ACOS|ATAN|TO|OF|AT|BY)\b', Keyword),
            (r'\b(TRUE|FALSE)\b', Keyword.Constant),
            (r'\b([A-Z_][A-Z0-9_.]*)\b', Name),
            (r'[\+\-\*\/\.\:\(\)\,\;\=\<\>\&\|\^]', Punctuation),
        ],

        'comment': [
            ('\(\*', Comment.Multiline, '#push'),
            ('\*\)', Comment.Multiline, '#pop'),
            ('[^*(]+', Comment.Multiline),
            ('[*(]', Comment.Multiline),
        ],

        'string' : [
            (r"\$(?:[$'LNPRT]|[0-9A-F]{2})", String.Escape),
            (r"[^'$]+", Literal.String),
            (r"'", Literal.String, '#pop'),
        ],
        
        'wstring' : [
            (r'\$(?:[$"LNPRT]|[0-9A-F]{4})', String.Escape),
            (r'[^"$]+', Literal.String),
            (r'"', Literal.String, '#pop'),
        ]
    }
