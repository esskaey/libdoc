"""
Encapsulate the logic for the content JSON file
"""

import base64
import codecs
import hashlib
import sys
import os
import json
import re
from collections.abc import Mapping, Sequence
from datetime import datetime
from abc import ABCMeta, abstractproperty, abstractmethod
from textwrap import wrap, dedent
import binascii

from typing import Dict, List, Tuple, Any

from pytz import utc, timezone
from babel.dates import format_datetime
from babel import Locale
from slugify import slugify

from . import core
from .exceptions import ContentError
from .core import escape_iec_names as se
from .transformer import create_builder_state, STATE

import hashlib
import base64

class PathMap:

    def __init__(self, hashing=False, slug=0):
        self._path_map = {}
        self._hashing = hashing
        self._slug = slug

    def hash(self, path, orig_name):
        if path == '' or not self._hashing:
            return path, orig_name
        xpath = path
        if isinstance(xpath, str):  # changed unicode to str
            xpath = xpath.encode('utf-8')
        hash_ = base64.urlsafe_b64encode(hashlib.sha1(xpath).digest())[:-1].decode()  # added decode()

        value = self._path_map.get(hash_)

        if value is None:
            self._path_map[hash_] = {'path': path, 'slug': {}}
        elif value['path'] != path:
            raise KeyError()

        name = orig_name.split('.')[-1]

        if self._slug == 0:
            return hash_, name

        slug = self.get_unique_slug(hash_, name)
        self._path_map[hash_]['slug'][name] = slug
        return hash_, slug

    def get_unique_slug(self, hash_, name):
        # provides path-wide unique slugified filename

        slug_candidate_name = name  # Assuming name is already slugified. Remove if you want to use slugify

        existing_slugs = self._path_map[hash_]['slug'].values()  # changed viewvalues() to values()
        suffix = ''
        while f"{slug_candidate_name}{suffix}" in existing_slugs:
            suffix = suffix + 1 if type(suffix) is int else 1

        return f"{slug_candidate_name}{suffix}"

    def get_hash(self, path, orig_name):
        if path == '' or not self._hashing:
            return path, orig_name.split('.')[-1]
        xpath = path
        if isinstance(xpath, str):  # changed unicode to str
            xpath = xpath.encode('utf-8')
        hash_ = base64.urlsafe_b64encode(hashlib.sha1(xpath).digest())[:-1].decode()  # added decode()

        value = self._path_map.get(hash_)
        slug = value['slug'].get(orig_name, orig_name)

        return hash_, slug

    def path(self, hash_):
        if hash_ == '' or not self._hashing:
            return hash_
        return self._path_map.get(hash_)['path']

    @property
    def mapping(self):
        return self._path_map.copy() if self._hashing else None

class Particle(ABCMeta):
    _path_map = None

    def __init__(self, content, key, element, path):
        if Particle._path_map is None:
            Particle._path_map = content._path_map

        self._content = content
        self._key = key
        self._element = element
        self._path, self._slug = Particle._path_map.hash(path, self.name)
        self._suffix = os.path.splitext(core.EXT_RST)[1]
        self._get_suffix = True
        self._master_doc = core.INDEX_RST
        self._get_master_doc = True

    @property
    def key(self):
        return self._key

    @abstractproperty
    def normalized_name(self):
        raise NotImplementedError

    @property
    def has_sub_particles(self):
        return len(list(self.children)) != 0

    @property
    def path(self):
        return self._path

    @property
    def target(self):
        return ".. _`{name}`:".format(name=self.name.replace(':', '.'))

    @abstractproperty
    def name(self):
        raise NotImplementedError

    @abstractproperty
    def type(self):
        raise NotImplementedError

    @abstractproperty
    def toc(self):
        raise NotImplementedError

    @abstractproperty
    def filename(self):
        raise NotImplementedError
    
    @abstractproperty
    def sub_particle_path(self):
        raise NotImplementedError

    def _substitute_filenames(self, doc):
        def process(m):
            key = m.group('key')
            file_name = self._content.external_files.get(key)
            if file_name:
                path = '/../' + file_name
            else:
                path = "** Unknown file reference: '@({})' **".format(key)
            return path

        return re.sub(core.FILE_PATH_REGEX, process, doc)

    @abstractproperty
    def doc(self):
        raise NotImplementedError

    @property
    def file_suffix(self):
        if self._get_suffix:
            config = self._content.config
            if config:
                self._suffix = config.get('source_suffix', self._suffix)
                self._get_suffix = False
        return self._suffix

    @property
    def children(self):
        if "Content" in self._element:
            for element in self._element["Content"]:
                if "Object" in element:
                    if element["Object"].split('.')[-2] == "Accessors":
                        continue
                yield element

    @property
    def master_doc(self):
        if self._get_master_doc:
            config = self._content.config
            if config:
                master_doc = os.path.splitext(core.INDEX_RST)[0]
                self._master_doc = config.get('master_doc', master_doc) + self.file_suffix
                self._get_master_doc = False
        return self._master_doc

    @property
    def is_kinematic_fb(self):
        return False



class OParticle(Particle):
    """
    JSON Objects
    """
    _dcl: str = os.path.splitext(core.EXT_DCL)[1]
    _imp: str = os.path.splitext(core.EXT_IMP)[1]

    def __init__(self, 
                 content: Any, 
                 key: Any, 
                 element: Dict, 
                 path: str, 
                 particle: Dict, 
                 inherited_particle_refs: List[Tuple[str, str, str, str, str]]):
        
        super().__init__(content, key, element, path)
        
        self._particle: Dict = particle
        self._inherited_particle_refs: Dict = {}
        
        for scope, parent_type, parent_name, child_area, name in inherited_particle_refs:
            self._inherited_particle_refs.setdefault(scope, {}).setdefault(parent_type, {}).setdefault(parent_name, {}).setdefault(child_area, []).append((parent_name, name))

    @property
    def has_inherited_particles(self) -> bool:
        return len(self._inherited_particle_refs) > 0

    @property
    def name(self) -> str:
        path = self._element["Object"].split('.')
        return '.'.join(e for i, e in enumerate(path) if i % 2 != 0)

    @property
    def normalized_name(self) -> str:
        return self._slug.split('.')[-1]

    @property
    def type(self) -> str:
        if "ObjectType" in self._particle:
            return self._particle["ObjectType"]
        else:
            raise ContentError("Unexpected object in content file")

    @property
    def dcl_filename(self) -> str:
        folder, names = self._element['Object'].split('.', 1)
        name = os.path.join(folder, '.'.join(core.normalize(name) for i, name in enumerate(names.split('.')) if i % 2 == 0))
        return name + OParticle._dcl

    @property
    def dcl(self) -> str:
        text = self._particle.get("STDeclaration", None)
        if text is not None:
            text = '\n'.join(line.rstrip() for line in dedent(str.expandtabs('\n'.join(text.splitlines()), tabsize=4)).splitlines())
        return text

    @property
    def imp_filename(self) -> str:
        folder, names = self._element['Object'].split('.', 1)
        name = os.path.join(folder, '.'.join(core.normalize(name) for i, name in enumerate(names.split('.')) if i % 2 == 0))
        return name + OParticle._imp

    @property
    def imp(self) -> str:
        text = self._particle.get("STImplementation", None)
        if text is not None:
            text = '\n'.join(line.rstrip() for line in dedent(str.expandtabs('\n'.join(text.splitlines()), tabsize=4)).splitlines())
        return text

    @property
    def filename(self) -> str:
        name = self.normalized_name
        return os.path.join(self.path, name + self.file_suffix)

    @property
    def sub_particle_path(self) -> str:
        path = os.path.join(Particle._path_map.path(self.path), f'pou-{self.name}')
        return Particle._path_map.hash(path, self._key)[0]

    @property
    def toc(self):
        keys = []
        toc = []
        name = core.normalize(self._element["Object"].split('.')[-1])
        if "Content" in self._element:
            for element in self.children:
                key = ''
                if "Object" in element:
                    key = element["Object"].split('.')[-1]
                    path = os.path.join(Particle._path_map.path(self._path), 'pou-' + name)
                    hash_path, slug = Particle._path_map.get_hash(path, key)
                    toc.append('/'.join(['', hash_path.replace('\\', '/'), slug]))
                elif "Folder" in element:
                    folder = key = core.normalize(element["Folder"])
                    path = os.path.join(Particle._path_map.path(self._path), 'pou-' + name, folder)
                    toc.append('/'.join(['', Particle._path_map.hash(path, self._key)[0].replace('\\', '/'), 'fld-' + folder]))
                keys.append(key)
            toc = list(zip(keys, toc))
            toc.sort(key=lambda k: k[0])
            toc = [x[1] for x in toc]
        return toc

    @property
    def declaration(self):
        particle = self._particle
        if "ReturnType" in particle and "ObjectType" in particle:
            modifiers = ''
            if "AccessModifiers" in particle and particle["AccessModifiers"]:
                modifiers = " " + " ".join([m.upper() for m in particle["AccessModifiers"]])
            text = "{0}{1} {2} : {3}".format(
                particle["ObjectType"].upper(), modifiers, particle["Name"], particle["ReturnType"])
        else:
            text = particle.get('Verbatim', '')
        if text:
            links = set()
            symbols = self._content.symbols
            if "Extends" in particle:
                symbol = particle["Extends"]["Class"]
                if symbol in symbols:
                    pattern = r'\b({0})\b'.format(re.escape(symbol))
                    text = re.sub(pattern, r"|d\1|", text, flags=re.UNICODE)
                    links.add(".. |d{0}| replace:: :ref:`{0}<{1}>`".format(symbol, symbols[symbol]))
            if "Implements" in particle:
                symbol_list = particle["Implements"]
                for symbol in symbol_list:
                    if symbol in symbols:
                        pattern = r'\b({0})\b'.format(re.escape(symbol))
                        text = re.sub(pattern, r"|d\1|", text, flags=re.UNICODE)
                        links.add(".. |d{0}| replace:: :ref:`{0}<{1}>`".format(symbol, symbols[symbol]))
            if "ReturnType" in particle:
                symbol = particle["ReturnType"]
                if symbol in symbols:
                    pattern = r'\b({0})\b'.format(re.escape(symbol))
                    text = re.sub(pattern, r"|d\1|", text, flags=re.UNICODE)
                    links.add(".. |d{0}| replace:: :ref:`{0}<{1}>`".format(symbol, symbols[symbol]))
            text = ' '.join([se(t) for t in text.split(' ')])
            text = "{0}\n\n{1}".format(text, '\n'.join(links))
        return text

    @property
    def iotbl(self):
        ml_pou_attributes = core.IOTBL_L_FB_ATTRIBUTES
        max_width = {'comment': sys.maxsize, 'type': sys.maxsize, 'initial': sys.maxsize}
        symbols = self._content.symbols

        pou_attributes = []
        for k, v in self._particle.get("Attributes", {}).iteritems():
            s = "{k} := {v}".format(k=k, v=v.get("Value", '')) if v else k
            pou_attributes.append(s)
            ml_pou_attributes = max(len(s), ml_pou_attributes)

        def check_comments(table_width):
            if table_width > core.IOTBL_MAX_TABLE_WIDTH:
                max_width.update({'comment': core.IOTBL_GOOD_COMMENT_WIDTH})
                return False
            return True

        def check_initials(table_width):
            if table_width > core.IOTBL_MAX_TABLE_WIDTH:
                max_width.update({'initial': core.IOTBL_GOOD_INITIAL_WIDTH})
                return False
            return True

        def check_types(table_width):
            if table_width > core.IOTBL_MAX_TABLE_WIDTH:
                max_width.update({'type': core.IOTBL_GOOD_TYPE_WIDTH})
                return False
            return True

        value = None
        # We need a table with a small as possible width, so we try to reach this goal three times
        for check_body in (check_comments, check_types, check_initials):
            body = []
            links = set()
            ml_attributes = ml_scope = ml_name = ml_type = 0
            ml_comment = ml_initial = ml_address = ml_inherited_from = 0

            dut = ''
            if "ObjectType" in self._particle:
                variables = self._particle.get("Variables", self._particle.get("Members", []))
                scopes = [('input',), ('constant', 'inOut'), ('inOut',), ('output',), ('return', 'output'), ('constant', 'global'),
                          ('global',), ('retain',), ('persistent',), ('empty',)]
                type_header = self._particle['ObjectType']
            else:
                raise ContentError('Unexpected item for iotbl')

            for variable in variables:
                scope = tuple(variable.get("Scope", ['empty']))
                if scope not in scopes:
                    continue

                if scope == ('constant', 'inOut'):
                    scope = 'Inout Const'
                else:
                    scope = scope[0].capitalize() if scope not in (('local',), ('empty',), ('global',)) else ''

                if scope == "Return":
                    name = se(variable.get("Name", ''))
                elif type_header in ("Enum", "GVL", "ParamList"):
                    # todo: evaluate {attribute 'qualified-access-only'}
                    # ".. index::\n   single: {name}\n   single: {parent}.{name}\n\n{symbol}"\
                    name = ".. _`{parent}.{name}`:\n\n" \
                           "{symbol}"\
                        .format(parent=self._particle["Name"],
                                name=variable.get("Name", ''),
                                symbol=se(variable.get("Name", '')))
                else:
                    # name = ":index:`{0}`".format(variable.get("Name", ''))
                    name = "{0}".format(se(variable.get("Name", '')))

                name = name.splitlines()
                ml_name = max(ml_name, core.IOTBL_L_NAME if name else 0, *[len(n) for n in name])

                typedef = variable.get("Type", {})
                if "Verbatim" in typedef and "BaseType" in typedef:
                    base_type = typedef["BaseType"]["Class"]
                    verbatim = typedef["Verbatim"]
                    if base_type in symbols and verbatim.find(base_type) != -1:
                        pattern = r'\b({0})\b'.format(re.escape(base_type))
                        o_type = re.sub(pattern, r"|io\1|", verbatim, flags=re.UNICODE)
                        links.add(".. |io{0}| replace:: :ref:`{0}<{1}>`".format(base_type, symbols[base_type]))
                    else:
                        o_type = ' '.join([se(t) for t in typedef.get("Verbatim", '').split(' ')])
                else:
                    o_type = typedef.get("Class", '')
                    if o_type in symbols:
                        link = "|io{0}|".format(o_type)
                        links.add(".. |io{0}| replace:: :ref:`{0}<{1}>`".format(o_type, symbols[o_type]))
                        o_type = link
                    else:
                        if "Verbatim" in typedef:
                            o_type = se(typedef["Verbatim"])
                        else:
                            o_type = se(o_type)

                comment = ''
                if scope == 'Return':
                    doc = self._raw_doc
                    si = doc.find(":return:")
                    if si != -1:
                        comment = doc[si + len(":return:"):]
                else:
                    if "Doc" in variable:
                        comment = variable["Doc"]
                    elif "Comment" in variable:
                        comment = variable["Comment"]

                if comment:
                    comment = self._substitute_filenames(comment)

                initial = ' '.join([se(i) for i in variable.get("Initial", '').split(' ')])
                if initial == '':
                    # Get the values from an enum as initials
                    initial = ' '.join([se(i) for i in variable.get("Value", '').split(' ')])
                    if initial.startswith('(') and initial.endswith(')'):
                        initial = initial[1:-1]

                address = variable.get("Address", '')
                symbol = variable.get("InheritedFrom", '')
                if symbol and symbol in symbols:
                    # inherited_from = ".. index::\n   single: Base; {0}\n\n|io{0}|".format(symbol)
                    inherited_from = "|io{0}|".format(symbol)
                    links.add(".. |io{0}| replace:: :ref:`{0}<{1}>`".format(symbol, symbols[symbol]))
                else:
                    inherited_from = se(symbol)

                inherited_from = inherited_from.splitlines()
                ml_inherited_from = max(ml_inherited_from,
                                        core.IOTBL_L_INHERITED_FROM if inherited_from else 0,
                                        *[len(n) for n in inherited_from])

                types = [o_type]
                local_max_with = max_width['type']
                if len(o_type) > local_max_with:
                    types = wrap(o_type, local_max_with, break_long_words=False)
                ml_type = max(ml_type, core.IOTBL_L_TYPE if o_type else 0, *[len(t) for t in types])

                comments = []
                if comment:
                    new_comment = comment
                    for match in re.finditer(core.SYMBOL_REF_REGEX, comment):
                        symbol = match.group(1)
                        if symbol in symbols:
                            pattern = r'\|({0})\|'.format(re.escape(symbol))
                            new_comment = re.sub(pattern, r"|io\1|", new_comment, flags=re.UNICODE)
                            links.add(".. |io{0}| replace:: :ref:`{0}<{1}>`".format(symbol, symbols[symbol]))
                    comments = OParticle.clean(new_comment)
                    if len(comments) == 1:
                        comment = comments[0]
                        local_max_with = max_width['comment']
                        if len(comment) > local_max_with:
                            comments = wrap(comment, local_max_with, break_long_words=False)
                    ml_comment = max(ml_comment, core.IOTBL_L_COMMENT, *[len(c) for c in comments])

                initials = [initial]
                if initial:
                    local_max_with = max_width['initial']
                    if len(initial) > local_max_with:
                        initials = wrap(initial, local_max_with)
                    ml_initial = max(ml_initial,
                                     core.IOTBL_L_VALUE if dut == 'Enum' else core.IOTBL_L_INITIAL,
                                     *[len(i) for i in initials])

                attributes = []
                for k, v in variable.get("Attributes", {}).iteritems():
                    s = "{k} := {v}".format(k=k, v=v.get("Value", '')) if v else k
                    attributes.append(s)
                    ml_attributes = max(len(s), ml_attributes, core.IOTBL_L_VR_ATTRIBUTES)
                if attributes:
                    attributes = wrap(', '.join(attributes),
                                      ml_attributes, break_long_words=False) if ml_attributes > 0 else []

                body.append(map(None, [scope], name, types, [address], initials,
                                comments, attributes, inherited_from))

                ml_scope = max(len(scope), ml_scope, core.IOTBL_L_SCOPE if scope else 0)
                ml_address = max(len(address), ml_address, core.IOTBL_L_ADDRESS if address else 0)

            value = {'type': type_header, 'title': self._particle["Name"],
                     'attributes': pou_attributes,
                     'header': [(core.IOTBL_FB_ATTRIBUTES, ml_pou_attributes), (core.IOTBL_SCOPE, ml_scope),
                                (core.IOTBL_NAME, ml_name), (core.IOTBL_TYPE, ml_type),
                                (core.IOTBL_ADDRESS, ml_address),
                                (core.IOTBL_VALUE if dut == 'Enum' else core.IOTBL_INITIAL, ml_initial),
                                (core.IOTBL_COMMENT, ml_comment), (core.IOTBL_VR_ATTRIBUTES, ml_attributes),
                                (core.IOTBL_INHERITED_FROM, ml_inherited_from)],
                     'body': body,
                     'links': links}

            body_ok = check_body(table_width=sum([ml_scope, ml_name, ml_type, ml_address,
                                                  ml_initial, ml_comment, ml_inherited_from]))
            if body_ok:
                break

        return value

    @property
    def prefix(self):
        prefix = ''
        text = self._raw_doc
        si = text.find(":prefix:")
        if si != -1:
            le = text.find("\n", si)
            if le == -1:
                prefix = text[si + len(":prefix:"):]
            else:
                prefix = text[si + len(":prefix:"):le]
        return prefix.strip()

    @classmethod
    def clean(cls, text):
        doc_list = []
        star_mode = False
        if text:
            # remove the comment for the prefix definition
            si = text.find(":prefix:")
            if si != -1:
                le = text.find("\n", si)
                if le == -1:
                    text = text[:si]
                else:
                    text = text[:si] + text[le:]

            # remove the comment for the return value
            si = text.find(":return:")
            if si != -1:
                text = text[:si]

            doc_list = [
                line.rstrip() for line in dedent(str.expandtabs('\n'.join(text.splitlines()), tabsize=4)).splitlines()
            ]

            # remove hanging empty lines
            nl = len(doc_list)
            for i, line in enumerate(reversed(doc_list), start=1):
                if not line:
                    del doc_list[nl - i]
                else:
                    break

            if len(doc_list) > 1 and doc_list[0].strip() != '' and doc_list[1].strip() == '':
                doc_list[0] = doc_list[0].strip()
                return doc_list

            if len(doc_list) > 0 and doc_list[0].lstrip().startswith('*'):
                return doc_list

            # remove leading '*'
            for i, line in enumerate(doc_list[1:], start=1):
                line = line.lstrip()
                if line.startswith('*'):
                    doc_list[i] = line[1:]
                    star_mode = True
                else:
                    break
            if star_mode:
                doc_list[1:] = dedent('\n'.join(doc_list[1:])).splitlines()

        return doc_list

    @property
    def _raw_doc(self):
        if "Doc" in self._particle:
            doc = self._particle["Doc"]
        elif "Comment" in self._particle:
            doc = self._particle["Comment"]
        else:
            doc = ""
        return '\n'.join(doc.splitlines())

    @property
    def doc(self):
        symbols = self._content.symbols
        symbol_refs = set()
        doc = self._substitute_filenames('\n'.join(OParticle.clean(self._raw_doc)))
        for match in re.finditer(core.SYMBOL_REF_REGEX, doc):
            symbol = match.group(1)
            if symbol in symbols:
                symbol_refs.add(".. |{0}| replace:: :ref:`{0}<{1}>`".format(symbol, symbols[symbol]))
        refs = '\n'.join([t for t in symbol_refs])
        return "{0}\n\n{1}".format(doc, refs) if refs else doc

    @property
    def is_kinematic_fb(self):
        return (self.type == "FunctionBlock" and
                "Attributes" in self._particle and
                core.KINEMATICS_ATTR in self._particle["Attributes"])

    @property
    def kinematic_header(self):
        symbols = self._content.symbols
        doc = self._substitute_filenames('\n'.join(OParticle.clean(self._raw_doc)))
        new_doc = doc
        for match in re.finditer(core.SYMBOL_REF_REGEX, doc):
            symbol = match.group(1)
            if symbol in symbols:
                pattern = r'\|({0})\|'.format(symbol)
                new_doc = re.sub(pattern, r"``\1``", new_doc, flags=re.UNICODE)
        return new_doc

    @property
    def kinematics_particle_id(self):
        return "{:08X}".format(binascii.crc32(self.name))

    @property
    def kinematic_params(self):
        params = []
        symbols = self._content.symbols

        if "ObjectType" in self._particle:
            variables = self._particle.get("Variables", [])
        else:
            raise ContentError('Unexpected item for iotbl')

        for variable in variables:
            scope = tuple(variable.get("Scope", ['empty']))
            if scope not in [('input',)]:
                continue
            name = variable.get("Name", '')

            typedef = variable.get("Type", {})
            param_type = typedef.get("Class", '')

            comment = ""
            if "Doc" in variable:
                comment = variable["Doc"]
            elif "Comment" in variable:
                comment = variable["Comment"]

            if comment:
                comment = self._substitute_filenames(comment)

            comments = []
            if comment:
                new_comment = comment
                for match in re.finditer(core.SYMBOL_REF_REGEX, comment):
                    symbol = match.group(1)
                    if symbol in symbols:
                        pattern = r'\|({0})\|'.format(symbol)
                        new_comment = re.sub(pattern, r"``\1``", new_comment, flags=re.UNICODE)
                comments = OParticle.clean(new_comment)

            params.append({'name': name, 'type': param_type, 'documentation': '\n'.join(comments)})

        return params

    @property
    def kinematic_images(self):
        images = [core.normalize(self.name) + '.svg']
        if "ObjectType" in self._particle:
            variables = self._particle.get("Variables", [])
        else:
            raise ContentError('Unexpected item for iotbl')

        particle_id = self.kinematics_particle_id
        for variable in variables:
            scope = tuple(variable.get("Scope", ['empty']))
            if scope not in [('input',)]:
                continue
            name = variable.get("Name", '')
            images.append("{}-{}.svg".format(core.normalize(name), particle_id))
        return images


class ATParticle(OParticle):
    """
    JSON Objects. Special cases for Actions and Transitions
    """
    @property
    def _raw_doc(self):
        doc = []
        head = True
        imp = self._particle.get('STImplementation')
        if imp:
            lines = [l.lstrip() for l in imp.splitlines()]
            for line in lines:
                if head and not line.startswith('//') and not line.startswith('///') and not line.startswith('(*'):
                    continue
                else:
                    if head:
                        if line.startswith('///'):
                            kind = '///'
                        elif line.startswith('//'):
                            kind = '//'
                        elif line.startswith('(*'):
                            kind = '(*'
                        else:
                            break
                        line = line.replace(kind, '', 1)
                        si = line.find('*)')
                        if si != -1:
                            doc.append(line[:si].strip())
                            break
                        doc.append(line.strip())
                    else:
                        if kind == '(*':
                            si = line.find('*)')
                            if si != -1:
                                doc.append(line[:si])
                                break
                            else:
                                doc.append(line)
                        elif line.startswith(kind):
                            doc.append(line.replace(kind, '', 1).strip())
                        else:
                            break
                    head = False
        return '\n'.join(doc)


class FParticle(Particle):
    """
    JSON Folder
    """
    @property
    def name(self):
        return self._element["Folder"]

    @property
    def normalized_name(self):
        return core.normalize(self._element["Folder"])

    @property
    def type(self):
        return "Folder"

    @property
    def filename(self):
        normalized_name = self.normalized_name
        return os.path.join(self.path, 'fld-' + normalized_name + self.file_suffix)

    @property
    def sub_particle_path(self):
        return self._path

    @property
    def target(self):
        name = self._key
        return ".. _`{name}`:".format(name=name[1:].replace(':', '.'))

    @property
    def toc(self):
        folder_check = set()
        keys = []
        toc = []
        if "Content" in self._element and self._element["Content"] is not None:
            for element in self.children:
                key = ''
                if "Object" in element:
                    #  todo: remove this if Visus are allowed
                    part = element["Object"].split('.')[0]
                    if part == "Visualizations":
                        continue
                    name = key = element["Object"].split('.')[-1]
                    path = Particle._path_map.path(self._path)
                    if path:
                        hash_path, slug = Particle._path_map.get_hash(path, name)
                        toc.append(
                            '/'.join(['', hash_path.replace('\\', '/'), slug]))
                    else:
                        # object in root are not slugified
                        toc.append('/'.join(['', core.normalize(name)]))
                elif "Folder" in element:
                    name = key = element["Folder"]
                    if name in folder_check:
                        raise ContentError("More then one folder with name '{name}' "
                                           "on the same level can't be handled properly".format(name=name))
                    folder_check.add(name)
                    normalized_name = core.normalize(name)
                    path = os.path.join(Particle._path_map.path(self._path), normalized_name)
                    if path:
                        toc.append(
                            '/'.join(['', Particle._path_map.hash(path, self._key)[0].replace('\\', '/'), 'fld-' + normalized_name]))
                    else:
                        toc.append('/'.join(['', 'fld-' + normalized_name]))
                keys.append(key)
            toc = zip(keys, toc)
            toc.sort(key=lambda k: k[0])
            toc = [x[1] for x in toc]
        return toc

    @property
    def doc(self):
        if "Doc" in self._element:
            symbols = self._content.symbols
            symbol_refs = set()
            text = str.expandtabs('\n'.join(self._element["Doc"].splitlines()), tabsize=4)
            doc = self._substitute_filenames(text)
            for match in re.finditer(core.SYMBOL_REF_REGEX, doc):
                symbol = match.group(1)
                if symbol in symbols:
                    symbol_refs.add(".. |{0}| replace:: :ref:`{0}<{1}>`".format(symbol, symbols[symbol]))
            refs = '\n'.join([t for t in symbol_refs])
            return "{0}\n\n{1}".format(doc, refs) if refs else doc
        else:
            return ""


class IParticle(FParticle):
    """
    JSON library index
    """
    @property
    def name(self):
        return self._element["Index"]

    @property
    def normalized_name(self):
        return core.normalize(self._element["Index"])

    @property
    def type(self):
        return "Index"

    @property
    def filename(self):
        return os.path.join(self.path, self.master_doc)

    @property
    def doc(self):
        text = str.expandtabs('\n'.join(self._content.info["ProjectInformation.Description"].splitlines()), tabsize=4)
        doc = self._substitute_filenames(text)
        if doc:
            symbols = self._content.symbols
            symbol_refs = set()
            for match in re.finditer(core.SYMBOL_REF_REGEX, doc):
                symbol = match.group(1)
                if symbol in symbols:
                    symbol_refs.add(".. |{0}| replace:: :ref:`{0}<{1}>`".format(symbol, symbols[symbol]))
            refs = '\n'.join([t for t in symbol_refs])
            return "{0}\n\n{1}".format(doc, refs) if refs else doc
        else:
            return ""


class Particles(Mapping):

    def __init__(self, particle_cache, particle_list):
        assert isinstance(particle_cache, Mapping)
        self._particle_cache = particle_cache
        assert isinstance(particle_list, Sequence)
        self._particle_list = particle_list

    def __getitem__(self, key):
        particle = self._particle_cache[key]
        assert isinstance(particle, Particle)
        return particle

    def __iter__(self):
        for particle in self._particle_list:
            yield particle.key

    def __len__(self):
        return len(self._particle_list)

    def itervalues(self):
        for particle in self._particle_list:
            yield particle

    def values(self):
        return self._particle_list[:]

    def keys(self):
        return self._particle_cache.keys()

    def iteritems(self):
        for particle in self._particle_list:
            yield (particle.key, particle)

    def items(self):
        return [(particle.key, particle) for particle in self._particle_list]


class ContentInfo(Mapping):

    def __init__(self, info):
        self._info = info
        self._file_header = info["FileHeader"]
        self._project_information = info["ProjectInformation"]

    def __getitem__(self, key):
        parts = ("FileHeader", "ProjectInformation")
        if '.' in key:
            part, key = key.split('.')
            if part in parts and key in self._info[part]:
                if part == "ProjectInformation":
                    return self._project_information[key]["Content"]
                else:
                    return self._file_header[key]
        else:
            for part in parts:
                    if key in self._info[part]:
                        if part == "ProjectInformation":
                            return self._project_information[key]["Content"]
                        else:
                            return self._file_header[key]
        return None

    def __len__(self):
        return len(self._project_information) + len(self._file_header)

    def __iter__(self):
        for key in self._file_header:
            yield "FileHeader.{0}".format(key)
        for key in self._project_information:
            yield "ProjectInformation.{0}".format(key)

    def __contains__(self, key):
        parts = ("FileHeader", "ProjectInformation")
        if '.' in key:
            part, key = key.split('.')
            return part in parts and key in self._info[part]
        else:
            for part in parts:
                if key in self._info[part]:
                    return True
        return False

    @property
    def info_table(self):

        ml_scope = ml_name = ml_type = ml_content = 0
        body = []

        for scope in ("FileHeader", "ProjectInformation"):
            for name, content in self._info[scope].iteritems():
                if scope == "ProjectInformation":
                    c_type = content["Type"]
                    if name == "Description" and content["Content"]:
                        content = "See: :ref:`Description <index_description>`"
                    else:
                        content = content["Content"]
                else:
                    if name == "creationDateTime":
                        c_type = "date"
                    elif name == "version":
                        c_type = "version"
                    else:
                        c_type = "string"

                contents = wrap(content, core.INFOTBL_GOOD_CONTENT_WIDTH, break_long_words=False)

                ml_scope = max(ml_scope, len(scope), core.INFOTBL_L_SCOPE)
                ml_name = max(ml_name, len(name), core.INFOTBL_L_NAME)
                ml_type = max(ml_type, len(c_type), core.INFOTBL_L_TYPE)
                ml_content = max(ml_content, core.INFOTBL_L_CONTENT, *[len(c) for c in contents])

                body.append(map(None, [scope], [name], [c_type], contents))

        value = {'header': [(core.INFOTBL_SCOPE, ml_scope), (core.INFOTBL_NAME, ml_name),
                            (core.INFOTBL_TYPE, ml_type), (core.INFOTBL_CONTENT, ml_content)],
                 'body': body}

        return value


class LibraryInfo(Mapping):

    def __init__(self, library):
        if "DefaultResolution" in library:
            match = re.search(core.LIB_REF_REGEX, library["DefaultResolution"])
            if match:
                group = match.groupdict()
                library.update(group)
        self._library = library

    def __getitem__(self, key):
        return self._library[key]

    def __iter__(self):
        return self._library.__iter__()

    def __len__(self):
        return len(self._library)


class Libraries(Mapping):

    def __init__(self, info):
        self._cache = {}
        for key, lib in info.iteritems():
            lib['Key'] = key
            self._cache[key] = LibraryInfo(lib)
        self._list = sorted(self._cache.values(), key=lambda x: x['Name'])

    def __getitem__(self, key):
        item = self._cache[key]
        return item

    def __iter__(self):
        for lib in self._list:
            yield lib['Key']

    def __len__(self):
        return len(self._list)


class Configuration(Mapping):
    def __init__(self, config_file_path):
        if not os.path.isfile(os.path.join(config_file_path, STATE)):
            create_builder_state(config_file_path)
        self._config = core.read_conf(config_file_path)

    def __len__(self):
        return len(self._config)

    def __iter__(self):
        for item in self._config:
            yield item

    def __getitem__(self, key):
        return self._config[key]

    def get(self, key, default=None):
        return self._config.get(key, default)


class Symbols(Mapping):

    def __init__(self, areas):

        def excluded_from_build(symbol):
            if "ObjectType" not in symbol:
                return True
            if "ObjectProperties" in symbol:
                for prop in symbol["ObjectProperties"]:
                    if prop["Name"] == "ExcludeFromBuildLocal" and prop["Value"] == "true":
                        return True
            return False

        self._symbols = {}
        for area in areas:
            for symbols in area.itervalues():
                # todo: remove this, after json is fixed
                if symbols is None or excluded_from_build(symbols):
                    continue
                object_type = symbols["ObjectType"]
                parent_name = symbols["Name"]
                parent_key = parent_name.upper()
                self._symbols[parent_key] = parent_name.replace(':', '.')
                for (current_type,
                     items,
                     qualified_only) in (("Enum", lambda x: x.get("Members", []), False),
                                         ("GVL", lambda x: x.get("Variables", []), False),
                                         ("ParamList", lambda x: x.get("Variables", []), False),
                                         ("FunctionBlock", lambda x: x.get("Methods", {}).itervalues(), True),
                                         ("FunctionBlock", lambda x: x.get("Properties", {}).itervalues(), True),
                                         ("Interface", lambda x: x.get("Methods", {}).itervalues(), True),
                                         ("Interface", lambda x: x.get("Properties", {}).itervalues(), True)):
                    if object_type != current_type:
                        continue
                    # todo: evaluate {attribute 'qualified-access-only'}
                    for item in items(symbols):
                        name = item["Name"]
                        key = name.upper()
                        qualified_name = "{0}.{1}".format(parent_name, name)
                        qualified_key = "{0}.{1}".format(parent_key, key)
                        self._symbols[qualified_key] = qualified_name.replace(':', '.')
                        # todo: reactivate this, after namespace issue is solved
                        # if "InheritedFrom" in item:
                        #   base_name = item["InheritedFrom"]
                        #   base_key = base_name.upper()
                        #   self._symbols[base_key] = base_name.replace(':', '.')
                        #   self._symbols["{0}.{1}".format(base_key, key)] = "{0}.{1}".format(base_name, name)
                        if not qualified_only:
                            # additional register global variables and enum members without prefix
                            self._symbols[key] = qualified_name.replace(':', '.')

    def add_symbol(self, symbol, target=None):
        if target is None:
            target = symbol
        assert isinstance(target, unicode)
        self._symbols[symbol.upper()] = target.replace(':', '.')

    def __getitem__(self, key):
        return self._symbols[key.upper()]

    def __len__(self):
        return self._symbols.__len__()

    def __iter__(self):
        for key in self._symbols:
            yield key


class ExternalFiles(Mapping):

    def __init__(self, files):
        self._files = {}
        if files is not None:
            for name, file in files.iteritems():
                if file['Embedded']:
                    self._files[name] = file['Filename']

    def __len__(self):
        return self._files.__len__()

    def __iter__(self):
        for file in self._files:
            yield file

    def __getitem__(self, key):
        return self._files[key]


class Content(object):

    def __init__(self, content_file_path, condensed=False, slug=0):
        with codecs.open(content_file_path, 'r', encoding='utf-8') as f:
            self._content = json.load(f)
        self._config_dir = os.path.dirname(content_file_path)
        self._content_file_name = os.path.basename(content_file_path)
        self._content["FileHeader"]["contentFile"] = os.path.basename(self._content_file_name)
        self._condensed = condensed
        self._path_map = PathMap(hashing=condensed, slug=slug)
        index_ref = {"Index": core.INDEX_RST, "Content": self._content["ProjectStructure"].get("Content")}
        self._particle_cache = {'.': IParticle(self, '.', index_ref, '')}
        self._content_info = ContentInfo({"FileHeader": self._content["FileHeader"],
                                          "ProjectInformation": self._content["ProjectInformation"]})
        self._libraries = Libraries(self._content["Libraries"])
        self._particle_list = [self._particle_cache['.']]
        self._particles = Particles(self._particle_cache, self._particle_list)
        self._config = None
        self._local_tz = None
        self._locale = None
        self._creation_dt = datetime.strptime(self._content["FileHeader"]["creationDateTime"],
                                              "%Y-%m-%dT%H:%M:%S").replace(tzinfo=utc)
        self._last_modification_dt = datetime.strptime(
            self._content["ProjectInformation"]["LastModificationDateTime"]["Content"],
            "%Y-%m-%dT%H:%M:%S").replace(tzinfo=utc)

        self._symbols = Symbols((self._content["DataTypes"], self._content["Interfaces"],
                                 self._content["POUs"], self._content["GlobalObjects"]))
        self._external_refs = {}
        self._external_files = ExternalFiles(self._content.get("ExternalFiles"))

        def traverse(elements, key='', path=''):
            for _element in elements:
                if "Object" in _element:
                    object_list = _element["Object"].split('.')
                    particle = self._content.get(object_list[0])
                    # todo: remove this after json is repaired
                    if particle is None:
                        continue
                    for item in object_list[1:]:
                        particle = particle.get(item)
                    # todo: remove this after json is repaired
                    if particle is None:
                        continue
                    name = object_list[-1]
                    new_key = key + '.' + name.replace(':', '.')
                    new_path = os.path.join(path, 'pou-' + core.normalize(name))
                    if "ObjectType" in particle and particle["ObjectType"] in {"Action", "Transition"}:
                        obj = ATParticle(self, new_key, _element, path, particle, set())
                    elif "ObjectType" in particle and particle["ObjectType"] in {
                        "Accessor",
                        "Visualization",
                        "TextList",
                        "ImagePool",
                        "ModuleDeclaration",
                        "GlobalTextList",
                        "GlobalImagePool"
                    }:  # todo: remove "Visualization" , "TextList, ..."
                        continue
                    else:
                        inherited_particle_refs = set()
                        for child_area in ("Methods", "Properties"):
                            if child_area not in particle:
                                continue
                            for inherited_particle in particle[child_area].itervalues():
                                if "InheritedFrom" not in inherited_particle:
                                    continue
                                name = inherited_particle["Name"]
                                parent_name = inherited_particle["InheritedFrom"]
                                parent_type = particle["ObjectType"]
                                parent_area = "POUs" if parent_type == "FunctionBlock" else "Interfaces"
                                if parent_name in self._content[parent_area]:
                                    scope = 'internal'
                                else:
                                    scope = 'external'
                                    if parent_type not in self._external_refs:
                                        self._external_refs[parent_type] = {}
                                    if parent_name not in self._external_refs[parent_type]:
                                        self._external_refs[parent_type][parent_name] = {}
                                    if child_area not in self._external_refs[parent_type][parent_name]:
                                        self._external_refs[parent_type][parent_name][child_area] = {}
                                    self._external_refs[parent_type][parent_name][child_area][name] = inherited_particle
                                inherited_particle_refs.add((scope, parent_type, parent_name, child_area, name))
                        obj = OParticle(self, new_key, _element, path, particle, inherited_particle_refs)
                elif "Folder" in _element:
                    name = _element["Folder"]
                    new_key = key + '.fld-' + name
                    new_path = os.path.join(path, core.normalize(name))
                    obj = FParticle(self, new_key, _element, new_path)
                    self._symbols.add_symbol(new_key[1:], new_key[1:].replace(':', '.'))
                else:
                    raise ContentError('Unexpected item in project structure')

                # noinspection PyTypeChecker
                self._particle_list.append(obj)
                self._particle_cache[new_key] = obj
                if "Content" in _element:
                    traverse(_element["Content"], new_key, new_path)

        element = self._content["ProjectStructure"]
        if "Content" in element:
            traverse(element["Content"])

    @property
    def symbols(self):
        return self._symbols

    @property
    def name(self):
        return self._content_file_name

    @property
    def info(self):
        return self._content_info

    @property
    def libraries(self):
        return self._libraries

    @property
    def particles(self):
        return self._particles

    @property
    def external_files(self):
        return self._external_files

    @property
    def condensed(self):
        return self._condensed

    @property
    def mapping(self):
        return self._path_map.mapping

    @property
    def config(self):
        assert isinstance(self._config, Configuration)
        return self._config

    @config.setter
    def config(self, config):
        assert isinstance(config, Configuration)
        self._config = config
        self._local_tz = timezone(self._config.get('timezone', 'Europe/Berlin'))
        self._locale = Locale.parse(self._config.get('locale', 'de_DE'))
        creation_dt = format_datetime(self._creation_dt, tzinfo=self._local_tz, locale=self._locale)
        self._content["FileHeader"]["creationDateTime"] = creation_dt
        last_modification_dt = format_datetime(self._last_modification_dt, tzinfo=self._local_tz, locale=self._locale)
        self._content["ProjectInformation"]["LastModificationDateTime"]["Content"] = last_modification_dt
