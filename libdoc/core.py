# -*- coding: utf-8 -*-
"""
Core
~~~~

The core module
All was is necessary...
"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
import json
import codecs
import os
import re
import sys
from string import ascii_letters, digits, maketrans
from unidecode import unidecode

from .exceptions import BuilderError, LibDocError

# Environment keys
LIBDOC_CODESYS = "LIBDOC_CODESYS"  #: Path and profile name of the responsible CODESYS.EXE
LIBDOC_TEMPLATES = "LIBDOC_TEMPLATES"  #: List of template locations (';' separated)
LIBDOC_THEME = "LIBDOC_THEME"  #: The theme folder location
LIBDOC_HHC = "LIBDOC_HHC"  #: Path of the responsible Microsoft HTML Help Compiler
PROGRAMFILES = "PROGRAMFILES"
LIBDOC_LOCALISATION = "LIBDOC_LOCALISATION"  #: comma separated list of language codes(e.g. "de, it, fr")
LIBDOC_SOURCE_LANGUAGE = "LIBDOC_SOURCE_LANGUAGE"  #: language of the reStruturedText files. Default: "en-US". Example: "de-DE"

# Filter constants
EXT_LIBRARY = "*.library"
EXT_JSON = "*.json"
EXT_CLEAN_JSON = "*.clean.json"
EXT_RST = "*.rst"
EXT_PY = "*.py"
EXT_DCL = "*.dcl"
EXT_IMP = "*.imp"
EXT_BAK = "*.bak"
EXT_LOG = "*.log"
EXT_LMD = "*.lmd"
EXT_POT = "*.pot"

# Magics
FRAME = 'Frame'  #: The name of the frame folder structure
MERGE_CACHE = '_merge_cache'  #: The name of the merge cache folder
LOCALE_DIR = '_locale'  #: The name of the localisation catalog folder
FRAME_SPECIALS = ('_static', '_templates')  #: The names of some special folders inside FRAME
SOURCE = 'Source'  #: The name of the source folder structure
CODE = 'Code'  #: The name of the folder for code snippets
BUILD = 'Build'  #: The name of the folder for build results
THEME = 'Theme'  #: The name of the folder for theme data
TEMPLATES = 'templates'  #: The name of the local templates folder
BINARIES = 'bin'  #: The name of the local binary utilities folder
CONF = 'conf.py'  #: The name of the sphinx-doc configuration file
CONF_TMP = 'conf.tmp'  #: The name of the temporary configuration file
INDEX_RST = 'index.rst'  #: The name of the root document
TODO_RST = 'todo.rst'  #: The name of the missing comment document
INFO_RST = 'info.rst'  #: The name of the file/project info document
LIBS_RST = 'libraries.rst'  #: The name of the libraries document
KINEMATIC_RST = 'kinematic.rst'  #: The name of the kinematic document
FRAME_JSON = 'frame.json'  #: The name of the frame info document
MANIFEST_JSON = 'manifest.json'  #: The name of the manifest document for lmd archives
CONFIG_JSON = 'config.json' # The name of the libdoc configuration file
SUPPORT_FILES = (INFO_RST, LIBS_RST)
PROFILE_PATH = ("CODESYS", "Profiles")  #: The path components to the profile folder
CODESYS_EXE_PATH = ("CODESYS", "Common", "CODESYS.EXE")  #: The path components for the CODESYS.EXE
PROFILE_FILTER = '*[1234567890].profile'  #: filter for pure CODESYS profiles
CODESYS_FILTER = '3S CODESYS*'  #: filter for the CODESYS folder structure
HHC_EXE_PATH = ('HTML Help Workshop', 'hhc.exe')
LOCALISATION_LIST = ('de', 'es', 'fr', 'it', 'ja', 'ru', 'zh_CHS')  #: default languages for localisation
KINEMATICS_ATTR = "sm_kin_libdoc"  #: The special attribute for kinematic-fb's
KINEMATICS = "_kinematics"  #: The name of the special folder for kinematics inside FRAME

# mapping CODESYS types to template names
TEMPLATE_NAMES = {'Action': 'act-object.rst',
                  'Accessor': 'accessor-object.rst',
                  'Alias': 'alias-object.rst',
                  'Enum': 'enum-object.rst',
                  'Folder': 'folder.rst',
                  'FunctionBlock': 'fb-object.rst',
                  'Function': 'fun-object.rst',
                  'GVL': 'gvl-object.rst',
                  'Index': 'index.rst',
                  'Interface': 'itf-object.rst',
                  'Method': 'meth-object.rst',
                  'ParamList': 'param-object.rst',
                  'Program': 'prg-object.rst',
                  'Property': 'prop-object.rst',
                  'Struct': 'struct-object.rst',
                  'Transition': 'trans-object.rst',
                  'Union': 'union-object.rst'}

# Regular expressions
CDS_VERSION_REGEX = r"V(?P<main>\d+)\.(?P<minor>\d+)( SP(?P<sp>\d+))?( Patch (?P<patch>\d+))?" \
                    r"( (Hotfix |HF)(?P<hotfix>\d+))?"
CDS_PROFILE_REGEX = re.compile(r"CODESYS {ver}\.{ext}".format(ver=CDS_VERSION_REGEX, ext="profile"), re.IGNORECASE)

MERGE_START_REGEX = re.compile(r'\s*(?:\.\.|#)\s+<%\s*merge\s*"(?P<key>.+)"\s*(?P<flag>-)?%>(?P<tail>.*)$', re.UNICODE)
MERGE_END_REGEX = re.compile(r'\s*(?:\.\.|#)\s+<%(?P<flag>-)?\s*endmerge\s*%>(?P<tail>.*)$', re.UNICODE)
MERGE_SET_REGEX = re.compile(r'\s*(?:\.\.|#)\s+<%\s*set\s+(?P<var>\w+)\s*=\s*(?P<expr>.+)\s*%>(?P<tail>.*)$', re.UNICODE)

LIB_REF_REGEX = re.compile(r'(?P<Name>.+),\s*(?P<Version>.+)\s*\((?P<Company>.+)\)', re.UNICODE)

SYMBOL_REF_REGEX = re.compile(r'(?<!\.\. )\|(?P<symbol>\S.*?)\|', re.UNICODE)

FILE_PATH_REGEX = re.compile(r'\B@\((?P<key>.+?)\)\B', re.UNICODE)

# header for iotbl
IOTBL_FB_ATTRIBUTES = IOTBL_VR_ATTRIBUTES = 'Attributes'
IOTBL_SCOPE = 'Scope'
IOTBL_NAME = 'Name'
IOTBL_TYPE = 'Type'
IOTBL_COMMENT = 'Comment'
IOTBL_INITIAL = 'Initial'
IOTBL_VALUE = 'Value'
IOTBL_ADDRESS = 'Address'
IOTBL_INHERITED_FROM = 'Inherited from'

IOTBL_L_VR_ATTRIBUTES = len(IOTBL_VR_ATTRIBUTES)
IOTBL_L_FB_ATTRIBUTES = len(IOTBL_FB_ATTRIBUTES)
IOTBL_L_ADDRESS = len(IOTBL_ADDRESS)
IOTBL_L_NAME = len(IOTBL_NAME)
IOTBL_L_TYPE = len(IOTBL_TYPE)
IOTBL_L_SCOPE = len(IOTBL_SCOPE)
IOTBL_L_INHERITED_FROM = len(IOTBL_INHERITED_FROM)
IOTBL_L_INITIAL = len(IOTBL_INITIAL)
IOTBL_L_VALUE = len(IOTBL_VALUE)
IOTBL_L_COMMENT = len(IOTBL_COMMENT)

IOTBL_MAX_TABLE_WIDTH = 100
IOTBL_GOOD_COMMENT_WIDTH = 60
IOTBL_GOOD_TYPE_WIDTH = 25
IOTBL_GOOD_INITIAL_WIDTH = 15

INFOTBL_SCOPE = 'Scope'
INFOTBL_NAME = 'Name'
INFOTBL_TYPE = 'Type'
INFOTBL_CONTENT = 'Content'

INFOTBL_L_SCOPE = len(INFOTBL_SCOPE)
INFOTBL_L_NAME = len(INFOTBL_NAME)
INFOTBL_L_TYPE = len(INFOTBL_TYPE)
INFOTBL_L_CONTENT = len(INFOTBL_CONTENT)

INFOTBL_GOOD_CONTENT_WIDTH = 50

VALID_FILENAME_CHARS = b'-_. {letters}{digits}'.format(letters=ascii_letters, digits=digits)
ALL_CHARS = maketrans(b'', b'')
WRONG_CHARS = b''.join(set(ALL_CHARS) - set(VALID_FILENAME_CHARS))
ALL_CHARS = ALL_CHARS.replace(b' ', b'-').replace(b'.', b'_')


def normalize(filename):
    """
    http://stackoverflow.com/questions/295135/turn-a-string-into-a-valid-filename-in-python
    """
    cleaned_filename = unidecode(filename).encode('ASCII', 'ignore')
    normalized_filename = cleaned_filename.translate(ALL_CHARS, WRONG_CHARS)
    return re.sub(r"(?P<vc>[._-])(?P=vc)+", r"\g<vc>", normalized_filename)


def escape_iec_names(name):
    assert isinstance(name, unicode)
    name = name.replace('_.', '\_.')
    if name.startswith('_'):
        name = '\_{n}'.format(n=name[1:])
    if name.endswith('_'):
        name = '{n}\_'.format(n=name[:-1])
    return name


def escape_folder_names(name):
    assert isinstance(name, unicode)
    return name.replace('.', '\.').replace('_', '\_').replace(':', '\:')


def read_conf(config_file_path):
    old_dir = os.getcwd()
    os.chdir(config_file_path)
    fs_encoding = sys.getfilesystemencoding()
    path = os.path.join(config_file_path, CONF).encode(fs_encoding)
    glb = {'__file__': path}
    conf = {}
    execfile(path, glb, conf)
    os.chdir(old_dir)
    return conf


def exec_hook(hook_file_path, args):
    if hook_file_path:
        glb = {}
        conf = {}
        old_dir = os.getcwd()
        os.chdir(os.path.dirname(hook_file_path))
        sys.argv = args
        execfile(hook_file_path, glb, conf)
        os.chdir(old_dir)


def get_version(version):
    return sum(
        [int(b) * [1000000, 100000, 1000, 1][int(a)] for (a, b) in enumerate(version.replace(' draft', '').split('.'))]
    )


def get_base_dir():
    if getattr(sys, 'frozen', False):
        # we are running in a |PyInstaller| bundle
        # noinspection PyProtectedMember
        basedir = sys._MEIPASS
    else:
        # we are running in a normal Python environment
        basedir = os.path.dirname(__file__)
    return basedir


def get_configuration():
    basedir = get_base_dir()
    conf_file_path = os.path.join(os.path.abspath(basedir), BINARIES, CONFIG_JSON)

    if conf_file_path is not None and os.path.isfile(conf_file_path):
        with codecs.open(conf_file_path, 'r', encoding='utf-8') as f:
            try:
                conf = json.load(f)
            except:
                raise LibDocError("Error during parsing configuration file %s" % conf_file_path)
        return conf
    return None
