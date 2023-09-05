# -*- coding: utf-8 -*-
"""
Merge
~~~~~

This module provide functionality for mering content and frame data
"""
import codecs
import os
import fnmatch
import io
import json
import re
import shutil

from jinja2 import Environment, FileSystemLoader

from . import core
import sys
from .exceptions import MergeError
from .content import Content, Configuration


def merge(content=None, frame=None, source=None, debug=False):
    """
    So we see what is merge
    """
    if content is None:
        files = fnmatch.filter(os.listdir('.'), core.EXT_JSON)
        if files:
            content = files[0]
    if content is None or not os.path.isfile(content) or not fnmatch.fnmatch(content, core.EXT_JSON):
        raise MergeError('Not able to find content: {content}'.format(content=content))
    content = os.path.abspath(content)

    if frame is None:
        frame = os.path.join(os.path.dirname(content), core.FRAME)
    if not os.path.isdir(frame):
        raise MergeError('Not able to find frame: {frame}'.format(frame=frame))

    if source is None:
        source = os.path.join(os.path.dirname(frame), core.SOURCE)
    if os.path.isdir(source):
        try:
            shutil.rmtree(source)
        except OSError:
            raise MergeError('Not able to delete source: {source}'.format(source=source))
    os.mkdir(source)

    content = Content(content)

    ext = os.path.splitext(core.EXT_JSON)[1]
    merge_cache = os.path.join(frame, core.MERGE_CACHE)
    cache_filename = os.path.join(merge_cache, "{name}{ext}".format(name=core.MERGE_CACHE, ext=ext))
    with codecs.open(cache_filename, 'r', encoding='utf-8') as f:
        cache = json.load(f)

    locations = os.environ.get(core.LIBDOC_TEMPLATES, "").split(';')
    locations = [l for l in locations if os.path.isdir(l)]
    basedir = core.get_base_dir()

    locations.append(os.path.join(os.path.abspath(basedir), core.TEMPLATES))
    env = Environment(loader=FileSystemLoader(locations), trim_blocks=True, lstrip_blocks=True)
    env.filters['se'] = core.escape_iec_names
    env.filters['fe'] = core.escape_folder_names

    # merge conf.py
    config_path = os.path.normpath(os.path.join(frame, os.path.pardir))
    config_file = os.path.join(config_path, core.CONF)
    _merge_file(config_file, config_file, content, cache, env, debug=debug)
    if not debug:
        content.config = Configuration(config_path)

    for dirpath, dirnames, filenames in os.walk(frame):
        if dirpath == frame:
            dirnames.remove(core.MERGE_CACHE)
            special_folders = list(core.FRAME_SPECIALS)
            if not debug:
                locale_dirs = content.config.get('locale_dirs')
                if locale_dirs is not None:
                    special_folders.extend(locale_dirs)
            for name in special_folders:
                if name not in dirnames:
                    continue
                frame_file = os.path.join(dirpath, name)
                source_file = os.path.join(source, os.path.relpath(dirpath, frame), name)
                shutil.copytree(frame_file, source_file)
                dirnames.remove(name)
        for name in dirnames:
            os.mkdir(os.path.join(source, os.path.relpath(dirpath, frame), name))
        for name in filenames:
            frame_file = os.path.join(dirpath, name)
            source_file = os.path.join(source, os.path.relpath(frame_file, frame))
            if fnmatch.fnmatch(name, core.EXT_RST):
                _merge_file(frame_file, source_file, content, cache, env, debug=debug)
            else:
                shutil.copyfile(frame_file, source_file)


def _merge_file(src, dst, content, cache, env, debug=False):
    text = io.StringIO()
    with io.open(src, 'r', encoding='utf-8') as f:
        print('reading:', src)
        spec_active = 0
        key = ''
        for lno, line in enumerate(f.readlines(), start=1):
            match = re.search(core.MERGE_SET_REGEX, line)
            if match:
                group = match.groupdict()
                text.write('{{% set {0[var]} = {0[expr]} %}}\n'.format(group))
                if group['tail']:
                    print(src, 'Warning: unexpected text after "set" tag in line', lno)
            elif not spec_active:
                match = re.search(core.MERGE_START_REGEX, line)
                if match is None:
                    text.write(line)
                    continue
                spec_active = 1
                group = match.groupdict()
                if group['tail']:
                    print(src, 'Warning: unexpected text after "merge" tag in line', lno)
                key = group['key']
            else:
                match = re.search(core.MERGE_START_REGEX, line)
                if match:
                    spec_active += 1
                    continue
                match = re.search(core.MERGE_END_REGEX, line)
                if match:
                    spec_active -= 1
                    if spec_active:
                        continue
                    text.write(cache[key])
                    group = match.groupdict()
                    if group['tail']:
                        print(src, 'Warning: unexpected text after "end-merge" tag in line', lno)
                    key = ''

    with io.open(dst, 'w', encoding='utf-8') as f:
        print('writing:', dst)
        value = text.getvalue()
        if debug:
            f.write(value)
        else:
            template = env.from_string(value)
            f.write(template.render({'content': content}))
        f.write('\n')
    text.close()
