# -*- coding: utf-8 -*-
"""
    A module...
"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
import codecs
import os
import fnmatch
import json
import re
import io

from . import core


def create_merge_cache(env, frame, force=False, exclude=None):
    if exclude is None:
        exclude = []

    mergecache = os.path.join(frame, core.MERGE_CACHE)
    try:
        os.mkdir(mergecache)
    except OSError:
        pass

    cache = {}
    ext = os.path.splitext(core.EXT_JSON)[1]
    cache_filename = os.path.join(mergecache, "{name}{ext}".format(name=core.MERGE_CACHE, ext=ext))

    if os.path.isfile(cache_filename) and not force:
        return

    for name in env.list_templates():
        if name in exclude:
            continue
        if not (fnmatch.fnmatch(name, core.EXT_RST) or fnmatch.fnmatch(name, core.EXT_PY)):
            continue
        template = env.get_template(name)
        template_filename = template.filename
        with io.open(template_filename, 'r', encoding='utf-8') as f:
            spec_active = 0
            text = None
            s_flag = False
            key = ''
            for lno, line in enumerate(f.readlines(), start=1):
                if not spec_active:
                    match = re.search(core.MERGE_START_REGEX, line)
                    if match is None:
                        continue
                    spec_active = 1
                    group = match.groupdict()
                    if group['tail']:
                        print(template_filename, 'Warning: unexpected text after "merge" tag in line', lno)
                    key = group['key']
                    s_flag = group['flag']
                    text = io.StringIO()
                else:
                    match = re.search(core.MERGE_START_REGEX, line)
                    if match:
                        spec_active += 1
                        continue
                    match = re.search(core.MERGE_END_REGEX, line)
                    if match is None:
                        text.write(line)
                        continue
                    else:
                        spec_active -= 1
                        if spec_active:
                            continue
                        group = match.groupdict()
                        e_flag = group['flag'] is not None
                        if group['tail']:
                            print(template_filename, 'Warning: unexpected text after "end-merge" tag in line', lno)
                        j = None if not s_flag else 1
                        k = None if not e_flag else -1
                        cache[key] = '\n'.join(text.getvalue().split('\n')[j:k])
                        text.close()

    with codecs.open(cache_filename, 'w', encoding='utf-8') as f:
        json.dump(cache, f, sort_keys=True, separators=(',', ': '), indent=4, ensure_ascii=False)
