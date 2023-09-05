# -*- coding: utf-8 -*-
"""
    Functionality for generating a fresh frame document
"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
import io
import os
import sys
import shutil
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from . import core
from .exceptions import FrameError
from .transformer import create_builder_state


def fresh(frame=None):

    if frame is None:
        config_path = os.path.abspath('.')
        frame = os.path.join(config_path, core.FRAME)
    else:
        frame = os.path.abspath(frame)
        config_path = os.path.dirname(frame)

    for folder in [core.BUILD, 'Images', os.path.basename(frame)]:
        try:
            os.mkdir(os.path.join(config_path, folder))
        except OSError:
            pass

    if frame is None or not os.path.isdir(frame):
        raise FrameError('Not able to find the frame structure')

    locations = os.environ.get(core.LIBDOC_TEMPLATES, "").split(';')
    locations = [l for l in locations if os.path.isdir(l)]
    basedir = core.get_base_dir()

    locations.append(os.path.join(os.path.abspath(basedir), core.TEMPLATES))
    env = Environment(loader=FileSystemLoader(locations), trim_blocks=True, lstrip_blocks=True)

    theme_template = os.environ.get(core.LIBDOC_THEME, os.path.join(os.path.abspath(basedir), 'themes'))
    theme_dir = os.path.join(config_path, core.THEME)
    if not os.path.isdir(theme_dir):
        shutil.copytree(theme_template, theme_dir)

    template = env.get_template('q_conf.py')
    template_file_name = os.path.join(config_path, core.CONF)
    with io.open(template_file_name, 'w', encoding='utf-8') as f:
        print('Generate:', template_file_name)
        now = datetime.now().replace(microsecond=0).isoformat(sep=b' ')
        ctx = {'frame': os.path.basename(frame), 'creationDateTime': now}
        f.write(template.render(ctx))
        f.write('\n')

    create_builder_state(config_path)

    template = env.get_template(core.TODO_RST)
    template_file_name = os.path.join(frame, core.TODO_RST)
    with io.open(template_file_name, 'w', encoding='utf-8') as f:
        print('Generate:', template_file_name)
        ctx = {}
        f.write(template.render(ctx))
        f.write('\n')

    template = env.get_template('q_index.rst')
    template_file_name = os.path.join(frame, core.INDEX_RST)
    with io.open(template_file_name, 'w', encoding='utf-8') as f:
        print('Generate:', template_file_name)
        ctx = {}
        f.write(template.render(ctx))
        f.write('\n')

    for name in core.FRAME_SPECIALS:
        try:
            os.mkdir(os.path.join(frame, name))
        except OSError:
            pass
