# -*- coding: utf-8 -*-
"""
Generate
~~~~~~~~

This module provide functionality for generating a frame document structure.
"""
import codecs
import json
import os
import fnmatch
import shutil
from datetime import datetime
import io

from jinja2 import Environment, FileSystemLoader

from . import core
from .exceptions import ContentError, FrameError
from .content import Content, Configuration
from .mergecache import create_merge_cache


def generate(content=None, frame=None, force=False, backup=False, condensed=False, slug=0):
    """
    | Try to find and load the content file in JSON format
    | Try to find or create the Frame folder
    | Generate a folder and file structure matching the ProjectStructure inside the content file
    """

    if content is None:
        files = fnmatch.filter(os.listdir('.'), core.EXT_JSON)
        if files:
            content = files[0]
    if content is None or not os.path.isfile(content) or not fnmatch.fnmatch(content, core.EXT_JSON):
        raise ContentError('Not able to find the content file')
    content = os.path.abspath(content)
    config_path = os.path.dirname(content)

    content = Content(content, condensed=condensed, slug=slug)
    content_info = content.info

    if frame is None:
        frame = os.path.join(config_path, core.FRAME)

    for folder in [core.CODE, core.BUILD, os.path.basename(frame)]:
        try:
            os.mkdir(os.path.join(config_path, folder))
        except OSError:
            pass

    if frame is None or not os.path.isdir(frame):
        raise FrameError('Not able to find the frame structure')

    code = os.path.join(config_path, core.CODE)

    locations = os.environ.get(core.LIBDOC_TEMPLATES, "").split(';')
    locations = [l for l in locations if os.path.isdir(l)]
    basedir = core.get_base_dir()

    locations.append(os.path.join(os.path.abspath(basedir), core.TEMPLATES))
    env = Environment(loader=FileSystemLoader(locations), trim_blocks=True, lstrip_blocks=True)
    env.filters['se'] = core.escape_iec_names
    env.filters['fe'] = core.escape_folder_names

    theme_template = os.environ.get(core.LIBDOC_THEME, os.path.join(os.path.abspath(basedir), 'themes'))
    theme_dir = os.path.join(config_path, core.THEME)
    if not os.path.isdir(theme_dir):
        shutil.copytree(theme_template, theme_dir)

    create_merge_cache(env, frame, force=force)

    sphinx_templates = [core.CONF]
    for template_name in sphinx_templates:
        template = env.get_template(template_name)
        particle_file_name = os.path.join(config_path, template_name)
        # the files in sphinx_templates should never overwritten!
        if not os.path.isfile(particle_file_name):
            with io.open(particle_file_name, 'w', encoding='utf-8') as f:
                print('Generate:', particle_file_name)
                now = datetime.now().replace(microsecond=0).isoformat(sep=' ')
                ctx = {'content': content, 'name': os.path.splitext(content_info["FileHeader.libraryFile"])[0],
                       'frame': os.path.basename(frame), 'creationDateTime': now, 'build': core.BUILD}
                f.write(template.render(ctx))
                f.write('\n')

    # the conf.py is now ready to use
    config = content.config = Configuration(config_path)

    support_files = core.SUPPORT_FILES
    if config.get("todo_include_todos"):
        support_files = (core.TODO_RST, ) + support_files

    bak = os.path.splitext(core.EXT_BAK)[1]

    for f in support_files:
        template = env.get_template(f)
        file_name = os.path.join(frame, f)
        if not os.path.isfile(file_name) or force or backup:
            if os.path.isfile(file_name) and backup:
                bak_file = file_name + bak
                try:
                    os.rename(file_name, bak_file)
                except OSError:
                    os.remove(bak_file)
                    os.rename(file_name, bak_file)
            with io.open(file_name, 'w', encoding='utf-8') as f:
                print('Generate:', file_name)
                ctx = {'content': content}
                f.write(template.render(ctx))
                f.write('\n')

    for name in core.FRAME_SPECIALS:
        try:
            os.mkdir(os.path.join(frame, name))
        except OSError:
            pass

    # Here we need to traverse the ProjectStructure an generate for every folder a folder in FRAME.
    # The folder documentation will placed in a ``fld-<name>.rst``.
    # Every sub folder will result in a sub folder and so on ...
    # Every object will result in a ``\*.rst`` file.
    # Every object type will rendered with its related template.

    kinematics = None
    for key, particle in content.particles.items():
        particle_type = particle.type

        if particle_type == "Folder":
            particle_path = os.path.join(frame, particle.sub_particle_path)
            if not os.path.isdir(particle_path) or force:
                try:
                    os.mkdir(particle_path)
                except OSError:
                    pass

        if particle_type != "Index":
            if particle.has_sub_particles:
                particle_path = os.path.join(frame, particle.sub_particle_path)
                if not os.path.isdir(particle_path) or force:
                    try:
                        os.mkdir(particle_path)
                    except OSError:
                        pass

        particle_list = [particle]
        #if particle_type not in ("Index", "Folder"):
        #    particle_list.extend(list(particle.inherited_particles.itervalues()))
        for current_particle in particle_list:
            particle_file_name = os.path.join(frame, current_particle.filename)
            if not os.path.isfile(particle_file_name) or force or backup:
                if os.path.isfile(particle_file_name) and backup:
                    bak_file = particle_file_name + bak
                    try:
                        os.rename(particle_file_name, bak_file)
                    except OSError:
                        os.remove(bak_file)
                        os.rename(particle_file_name, bak_file)
                with io.open(particle_file_name, 'w', encoding='utf-8') as f:
                    print('Generate:', particle_file_name)
                    template = env.get_template(core.TEMPLATE_NAMES[current_particle.type])
                    ctx = {'content': content, 'key': current_particle.key}
                    f.write(template.render(ctx))
                    f.write('\n')

            if current_particle.is_kinematic_fb:
                if kinematics is None:
                    kinematics = {"name": "Kinematics Extension",
                                  "description": "This extension describes the kinematics configuration.",
                                  "data": [{}]}
                kinematics_path = os.path.join(frame, core.KINEMATICS)
                if not os.path.isdir(kinematics_path) or force:
                    try:
                        os.mkdir(kinematics_path)
                    except OSError:
                        pass
                particle_path = os.path.join(kinematics_path, core.normalize(current_particle.normalized_name))
                if not os.path.isdir(particle_path) or force:
                    try:
                        os.mkdir(particle_path)
                    except OSError:
                        pass

                current_kinematic = []

                particle_file_name = os.path.join(particle_path, os.path.basename(current_particle.filename))
                kinematic_location = os.path.join(core.KINEMATICS, os.path.splitext(os.path.relpath(particle_file_name, kinematics_path))[0] + '.html').replace('\\', '/')
                if not os.path.isfile(particle_file_name) or force or backup:
                    if os.path.isfile(particle_file_name) and backup:
                        bak_file = particle_file_name + bak
                        try:
                            os.rename(particle_file_name, bak_file)
                        except OSError:
                            os.remove(bak_file)
                            os.rename(particle_file_name, bak_file)
                    with io.open(particle_file_name, 'w', encoding='utf-8') as f:
                        print('Generate:', particle_file_name)
                        template = env.get_template('kin_header.rst')
                        ctx = {'content': content, 'particle': current_particle}
                        f.write(template.render(ctx))
                        f.write('\n')
                image = os.path.splitext(os.path.basename(particle_file_name))[0] + '.svg'
                particle_file_name = os.path.join(os.path.dirname(particle_file_name), image)
                kinematic_image = os.path.join('_images', image).replace('\\', '/')
                with io.open(particle_file_name, 'w', encoding='utf-8') as f:
                    print('Generate:', particle_file_name)
                    template = env.get_template('kin_img.svg')
                    ctx = {'content': content, 'particle': current_particle}
                    f.write(template.render(ctx))
                    f.write('\n')
                current_kinematic.append({'name': current_particle.name, 'location': kinematic_location, 'image': kinematic_image})

                params = current_particle.kinematic_params
                for param in params:
                    kinematic_name = "{}-{}.rst".format(core.normalize(param['name']), current_particle.kinematics_particle_id)
                    param_file_name = os.path.join(particle_path, kinematic_name)
                    kinematic_location = os.path.join(core.KINEMATICS, os.path.splitext(os.path.relpath(param_file_name, kinematics_path))[0] + '.html').replace('\\', '/')
                    if not os.path.isfile(param_file_name) or force or backup:
                        if os.path.isfile(param_file_name) and backup:
                            bak_file = param_file_name + bak
                            try:
                                os.rename(param_file_name, bak_file)
                            except OSError:
                                os.remove(bak_file)
                                os.rename(param_file_name, bak_file)
                        with io.open(param_file_name, 'w', encoding='utf-8') as f:
                            print('Generate:', param_file_name)
                            template = env.get_template('kin_param.rst')
                            ctx = {'content': content, 'particle': current_particle, 'param': param}
                            f.write(template.render(ctx))
                            f.write('\n')
                    image = os.path.splitext(os.path.basename(param_file_name))[0] + '.svg'
                    param_file_name = os.path.join(os.path.dirname(param_file_name), image)
                    kinematic_image = os.path.join('_images', image).replace('\\', '/')
                    with io.open(param_file_name, 'w', encoding='utf-8') as f:
                        print('Generate:', param_file_name)
                        template = env.get_template('kin_img.svg')
                        ctx = {'content': content, 'particle': current_particle, 'param': param}
                        f.write(template.render(ctx))
                        f.write('\n')
                    current_kinematic.append({'name': param['name'], 'location': kinematic_location, 'image': kinematic_image})

                kinematics["data"][0].update({current_particle.name: current_kinematic})

                kinematic_file_name = os.path.join(particle_path, core.KINEMATIC_RST)
                if not os.path.isfile(kinematic_file_name) or force or backup:
                    if os.path.isfile(kinematic_file_name) and backup:
                        bak_file = kinematic_file_name + bak
                        try:
                            os.rename(kinematic_file_name, bak_file)
                        except OSError:
                            os.remove(bak_file)
                            os.rename(kinematic_file_name, bak_file)
                    with io.open(kinematic_file_name, 'w', encoding='utf-8') as f:
                        print('Generate:', kinematic_file_name)
                        template = env.get_template('kinematic.rst')
                        ctx = {'content': content, 'particle': current_particle,
                               'images': current_particle.kinematic_images}
                        f.write(template.render(ctx))
                        f.write('\n')

        if particle_type not in ("Index", "Folder"):
            # generate *.dcl and *.imp files in the Code folder
            dcl_snipped_file_name = os.path.join(code, particle.dcl_filename)
            imp_snipped_file_name = os.path.join(code, particle.imp_filename)
            for file_name, txt in ((dcl_snipped_file_name, particle.dcl), (imp_snipped_file_name, particle.imp)):
                if txt is None:
                    continue
                try:
                    os.makedirs(os.path.dirname(file_name))
                except OSError:
                    pass
                with io.open(file_name, 'w', encoding='utf-8') as f:
                    print('Generate:', file_name)
                    f.write(txt)

    frame_file_name = os.path.join(frame, core.FRAME_JSON)
    if not os.path.isfile(frame_file_name) or force:
        print('Generate:', frame_file_name)
        manifest = {'header': {'name': core.FRAME_JSON,
                               'version': '0.0.0.5',
                               'created': datetime.utcnow().replace(microsecond=0).isoformat(),
                               'layout': 'condensed' if content.condensed else 'standard'},
                    'library': {'file': content_info["libraryFile"],
                                'title': content_info["Title"],
                                'version': content_info["Version"],
                                'company': content_info["Company"]}}
        mapping = {k: v['path'] for k, v in content.mapping.items()}
        if mapping is not None:
            manifest.update({'mapping': mapping})
        if kinematics is not None:
            manifest.update({'extensions': {'kinematics': kinematics}})
        with codecs.open(frame_file_name, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=4, separators=(',', ': '), sort_keys=True, ensure_ascii=False)

    return 0
