# -*- coding: utf-8 -*-
"""
Clean
~~~~~

The clean module provides functionality for removing some specified parts of a JSON file.
"""

from collections.abc import Sequence  # Changed from collections to collections.abc
import os
import fnmatch
import json

from . import core
from .exceptions import ContentError

class Cleaner(object):
    """
    Evaluate a configuration and remove the specified parts.

    :param conf_file_path: Optional. The path where the configuration is placed.
                           If the file exists, it will used.
                           Otherwise a default configuration ist generated.
    :param areas: Optional. Defaults to ``["DataTypes", "Interfaces", "GlobalObjects", "POUs"]``
    """

    def __init__(self, conf_file_path=None, areas=None):
        self._content = None
        self._conf = None

        if conf_file_path is not None and os.path.isfile(conf_file_path):
            with open(conf_file_path, 'r', encoding='utf-8') as f:
                self._conf = json.load(f)
        else:
            self._conf = {
                'exclude': {
                    'attribute': [('hide', '*'), ('conditionalshow', '*')],  # default setting
                    #'attribute': ['hide', 'conditionalshow'], # typical simplified; without values
                    #'attribute': [('*', '*')], # exclude all nodes with attributes, strongest action
                    'keyword': ['PRIVATE', 'INTERNAL'],
                    # 'folder': [],
                    # 'symbol': []
                },
                'include': {
                    'attribute': [],
                    'keyword': [],
                    # 'folder': [],
                    # 'symbol': []
                },
                'filter': {
                     # 'attribute': [] # remove no attribute
                     # 'attribute': [('myattribute', 'myvalue')] # remove attribute with specified value
                     # 'attribute': [('myattribute', 'myvalue'), ('myattribute2', 'myvalue2')]  # remove several attributes with specified values
                     # 'attribute': [('myattribute', '*')]  # remove specified attribute with arbitrary or no value
                     'attribute': [('*', '*')]  # remove all attributes, default setting
                },
                'preserve': {
                    # 'attribute': [('myattribute', '*')]
                    'attribute': [("sm_kin_libdoc", "*")]  # preserve kinematic attributes, default setting
                }
            }

        self._all = set()
        self._include = set()
        self._exclude = set()

        check_attribute_include = "include" in self._conf and "attribute" in self._conf["include"]
        check_attribute_exclude = "exclude" in self._conf and "attribute" in self._conf["exclude"]
        check_attribute_filter = "filter" in self._conf and "attribute" in self._conf["filter"]
        check_attribute_preserve = "preserve" in self._conf and "attribute" in self._conf["preserve"]
        self._include_attributes = self._conf["include"]["attribute"] if check_attribute_include else []
        self._exclude_attributes = self._conf["exclude"]["attribute"] if check_attribute_exclude else []
        self._filter_attributes = self._conf["filter"]["attribute"] if check_attribute_filter else []
        self._preserve_attributes = self._conf["preserve"]["attribute"] if check_attribute_preserve else []

        check_keyword_include = "include" in self._conf and "keyword" in self._conf["include"]
        check_keyword_exclude = "exclude" in self._conf and "keyword" in self._conf["exclude"]
        self._include_keywords = self._conf["include"]["keyword"] if check_keyword_include else []
        self._exclude_keywords = self._conf["exclude"]["keyword"] if check_keyword_exclude else []

        self._areas = areas or ["DataTypes", "Interfaces", "GlobalObjects", "POUs"]
        self._sub_areas = ["Methods", "Properties", "Actions", "Transitions"]

    def _check_attributes(self, path, particle):
        if "Attributes" in particle:
            for collection, attributes in [(self._include, self._include_attributes),
                                           (self._exclude, self._exclude_attributes)]:
                # process the attribute action
                for attribute_def in attributes:
                    if not attribute_def:
                        continue
                    if isinstance(attribute_def, Sequence):
                        name = attribute_def[0]
                        value = attribute_def[1] if len(attribute_def) > 1 else None
                    else:
                        name = attribute_def
                        value = None
                    if name == '*':
                        # exclude whole particle
                        self._exclude.add(".".join([path, particle["Name"]]))
                        break
                    if name in particle["Attributes"]:
                        attribute = particle["Attributes"][name]
                        if value is None or value == '*' or value == attribute.get("Value"):
                            collection.add(".".join([path, particle["Name"]]))

            # process attributes appearing (whether it appears at all)
            for filter_attribute in self._filter_attributes:
                if not filter_attribute:
                    # no attribute to remove
                    break
                name = filter_attribute[0]
                value = filter_attribute[1] if len(filter_attribute) > 1 else None
                if name == '*':
                    # remove all attributes, but respect objections
                    if self._preserve_attributes:
                        for attr_name in particle["Attributes"]:
                            if not any(attr_name == x[0] for x in self._preserve_attributes if x):
                                self._exclude.add(".".join([path, particle["Name"], "Attributes", attr_name]))
                    else:
                        self._exclude.add(".".join([path, particle["Name"], "Attributes"]))
                        break
                if name in particle["Attributes"]:
                    # remove specified attribute
                    attribute = particle["Attributes"][name]
                    if value is None or value == '*' or value == attribute.get("Value"):
                        self._exclude.add(".".join([path, particle["Name"], "Attributes", name]))

    def _check_members(self, members_list):
        candidates = []
        for member in members_list:
            member_is_candidate = False
            if "Attributes" in member:
                attributes = member["Attributes"]
                for attribute in attributes:
                    value = attributes[attribute]
                    value = value.get("Value") if value else None
                    for exclude_attribute in self._exclude_attributes:
                        if isinstance(exclude_attribute, Sequence):
                            excl_attr_name = exclude_attribute[0]
                            excl_attr_value = exclude_attribute[1] if len(exclude_attribute) > 1 else None
                        else:
                            excl_attr_name = exclude_attribute
                            excl_attr_value = None
                        if attribute == excl_attr_name:
                            if excl_attr_value is None or excl_attr_value == '*' or excl_attr_value == value:
                                candidates.append(member)
                                member_is_candidate = True
                                break
                    if member_is_candidate:
                        break

        for c in candidates:
            members_list.remove(c)

        for member in members_list:
            if "Attributes" in member:
                attrs = member["Attributes"]
                for filter_attribute in self._filter_attributes:
                    if not filter_attribute:
                        # no attribute to remove
                        break
                    name = filter_attribute[0]
                    value = filter_attribute[1] if len(filter_attribute) > 1 else None
                    if name == '*':
                        # remove all attributes
                        del member["Attributes"]
                        break
                    if name in attrs:
                        # remove specified attribute
                        attribute = attrs[name]
                        if value is None or value == '*' or value == attribute.get("Value"):
                            del attrs[name]

    def _check_keywords(self, path, particle):
        if "AccessModifiers" in particle:
            for collection, keywords in [(self._include, self._include_keywords),
                                         (self._exclude, self._exclude_keywords)]:
                modifiers = particle["AccessModifiers"]
                for modifier in modifiers:
                    if modifier.upper() in keywords:
                        collection.add(".".join([path, particle["Name"]]))

    def _check_all(self, path, element):
        if "Attributes" in element:
            self._check_attributes(path, element)
        if "AccessModifiers" in element:
            self._check_keywords(path, element)
        if "Variables" in element:
            members_list = element["Variables"]
            self._check_members(members_list)
        if "Members" in element:
            members_list = element["Members"]
            self._check_members(members_list)

    def _clean_structure(self, structure):
        for struct in structure:
            if "Content" in struct:
                child = struct["Content"]
                self._clean_structure(child)
                if not child:
                    del struct["Content"]
            if "Object" in struct:
                path = struct["Object"]
                if path in self._exclude:
                    if "Content" in struct:
                        del struct["Content"]
                    del struct["Object"]
            if "Folder" in struct and "Content" not in struct:
                del struct["Folder"]
            if "Doc" in struct and "Content" not in struct:
                del struct["Doc"]
        structure[:] = [s for s in structure if s]

    def dump_conf(self, conf_file_path):
        """
        Generate a JSON file with the current configuration.

        :param conf_file_path: The path where the configuration is placed
        :return: None
        """
        with open(conf_file_path, 'w', encoding='utf-8') as f:
            json.dump(self._conf, f, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False)

    def clean(self, content_file_path):
        """
        | Traverse the data structure in the specified JSON file.
        | Evaluate the the current configuration.
        | Remove the specified parts of the data structure.

        :param content_file_path: path to the JSON file containing the data structure
        :return: The cleaned data structure
        """
        with open(content_file_path, 'r', encoding='utf-8') as f:
            self._content = json.load(f)

        for area in self._areas:
            particles = self._content[area]
            for particle in particles.values():
                self._all.add(".".join([area, particle["Name"]]))
                for sub in self._sub_areas:
                    if sub in particle:
                        path = ".".join([area, particle["Name"], sub])

                        for child in particle[sub].values():
                            self._all.add('.'.join([path, child["Name"]]))

                            if sub == "Properties":
                                if "Accessors" in child:
                                    for accessor in child["Accessors"]:
                                        acc = child["Accessors"][accessor]
                                        acc_path = ".".join([path, child["Name"], "Accessors"])
                                        self._all.add(".".join([acc_path, acc["Name"]]))

                                        self._check_all(acc_path, acc)

                            self._check_all(path, child)

                self._check_all(area, particle)

        self._exclude = self._exclude - self._include

        structure = self._content["ProjectStructure"].get("Content")
        if structure:
            self._clean_structure(structure)

        paths = sorted(self._exclude, key=lambda x: x.count('.'), reverse=True)
        for path in paths:
            parts = path.split('.')
            particle = self._content
            for part in parts[:-1]:
                particle = particle[part]
            part = parts[-1]
            del particle[part]
        return self._content


def clean(content=None, clean_content=None):
    """
    Tries to remove (clean) some parts of the original content
    and generate a cleaned version of the original file.

    :param content: Optional. The path to the original JSON file. If content is None,
                    we try to use the first content file in the current working directory.
    :param clean_content: Optional. The path to the cleaned version of the JSON file.
                          If clean_content is None, we try to set it to ``./<content>.clean.json``
    :return: 0 = successful
    """
    if content is None:
        files = fnmatch.filter(os.listdir('.'), core.EXT_JSON)
        for f in files:
            if not fnmatch.fnmatch(f, core.EXT_CLEAN_JSON):
                content = f
                break

    if content is None or not os.path.isfile(content) or not fnmatch.fnmatch(content, core.EXT_JSON):
        raise ContentError('Not able to find the content file')
    content = os.path.abspath(content)

    conf_file = os.path.join(os.path.dirname(content), 'clean.conf')

    if clean_content is None:
        content_base_name = '.'.join([c for c in content.split('.') if c not in ['clean', 'json']])
        clean_content = "{0}.clean{1}".format(content_base_name, os.path.splitext(content)[1])
    clean_content = os.path.abspath(clean_content)

    cleaner = Cleaner(conf_file_path=conf_file)
    content = cleaner.clean(content)
    if not os.path.isfile(conf_file):
        cleaner.dump_conf(conf_file)

    with open(clean_content, 'w', encoding='utf-8') as f:
        json.dump(content, f, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False)

    return 0
