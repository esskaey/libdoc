# -*- coding: utf-8 -*-
"""
Make
~~~~

    +---------+--------+-----------+-----------+-----------+
    | Output  |  json  |   html    |    chm    |    lmd    |
    +---------+        +           +           +           +
    | Input   |        |           |           |           |
    +=========+========+===========+===========+===========+
    | library | export | transform | transform | transform |
    +---------+--------+-----------+-----------+-----------+
    | json    |   X    | transform | transform | transform |
    +---------+--------+-----------+-----------+-----------+
"""

import codecs
import fnmatch
import json
import os
import shutil

from translate.convert import convert
from translate.storage import po
from translate.convert.po2xliff import po2xliff
from translate.convert.xliff2po import convertxliff
from translate.tools.pocompile import convertmo

from . import core
from .export import export
from .clean import clean
from .generate import generate
from .transform import transform
from .exceptions import MakeError, BuilderError


INPUT_EXT = ['library', 'json']
OUTPUT_EXT = ['json', 'html', 'chm', 'lmd']
TRANSITIONS = {
    ('library', 'html'), ('library', 'chm'), ('library', 'lmd'),
    ('json', 'html'), ('json', 'chm'), ('json', 'lmd'),
}


def _export(library, json=None):
    if json is None:
        name = '{0}{1}'.format(os.path.splitext(os.path.basename(library))[0], os.path.splitext(core.EXT_JSON)[1])
        json = os.path.join(os.path.dirname(library), name)
    export(library, json)
    return json if os.path.isfile(json) else None


def _clean(content, clean_content=None):
    if clean_content is None:
        name = "{content[0]}.clean{content[1]}".format(content=os.path.splitext(content))
        clean_content = os.path.join(os.path.dirname(content), name)
    clean(content, clean_content)
    return clean_content if os.path.isfile(clean_content) else None


def _generate(content, frame=None, condensed=True):
    if frame is None:
        config_path = os.path.dirname(content)
        frame = os.path.join(config_path, core.FRAME)
    if os.path.isdir(frame):
        for f in os.listdir(frame):
            old = os.path.join(frame, f)
            if os.path.isfile(old) and fnmatch.fnmatch(f, '*.rst'):
                os.remove(old)
            if os.path.isdir(old):
                shutil.rmtree(old)
    generate(content, frame, force=True, condensed=condensed, slug=16)
    return frame if os.path.isfile(os.path.join(frame, core.FRAME_JSON)) else None


def _transform(builder, frame, product=None):
    config_path = os.path.normpath(os.path.join(frame, os.path.pardir))
    build_path = os.path.join(config_path, core.BUILD, os.path.basename(frame))
    if builder == 'chm':
        config = core.read_conf(config_path)
        basename = config.get('htmlhelp_basename', 'libdoc')
        result = os.path.join(build_path, 'chm', '{basename}.chm'.format(basename=basename))
    elif builder == 'html':
        result = os.path.join(build_path, 'html', 'index.html')
    elif builder == 'lmd':
        with codecs.open(os.path.join(frame, 'frame.json'), 'r', encoding='utf-8') as f:
            frame_data = json.load(f)
        if not frame_data:
            return None
        lib_data = frame_data['library']
        lmd_file = "{0}.{1}".format(os.path.splitext(lib_data['file'])[0], 'lmd')
        result = os.path.join(build_path, 'lmd', lmd_file)
    else:
        raise BuilderError('The {builder} format is not supported'.format(builder=builder))

    if product is None:
        product = result

    build = os.path.join(config_path, core.BUILD, os.path.basename(frame), builder)
    try:
        shutil.rmtree(build)
    except OSError:
        pass

    transform(builder, frame)
    if product != result:
        if builder in ['chm', 'lmd']:
            if os.path.isfile(product):
                try:
                    os.remove(product)
                except OSError:
                    return None
            shutil.copyfile(result, product)
        elif builder == 'html':
            src = os.path.dirname(result)
            dst = product
            if os.path.isdir(dst):
                try:
                    shutil.rmtree(dst)
                except OSError:
                    return None
            try:
                shutil.copytree(src, dst)
            except OSError:
                return None
        else:
            raise BuilderError('The {builder} format is not supported'.format(builder=builder))
    return product if os.path.isfile(product) or os.path.isdir(product) else None


def convertpo(inputfile, outputfile, templatefile):
    """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
    inputstore = po.pofile(inputfile)
    if inputstore.isempty():
        return 0
    convertor = po2xliff()
    outputstring = convertor.convertstore(inputstore, templatefile)
    source_language = os.environ.get(core.LIBDOC_SOURCE_LANGUAGE)
    if source_language is not None:
        outputstring = outputstring.replace(b'source-language="en-US"', b'source-language="{}"'.format(source_language))
    outputfile.write(outputstring)
    return 1


def _po2xliff(locale, xliff=None):
    formats = {"po": ("xlf", convertpo)}
    parser = convert.ConvertOptionParser(
        formats,
        usetemplates=False,
        description="Convert Gettext PO localization files to XLIFF localization files."
    )
    parser.run(['--errorlevel=exception', locale, xliff])
    return 0


def _xliff2po(xliff, locale=None):
    formats = {"xlf": ("po", convertxliff)}
    parser = convert.ConvertOptionParser(
        formats,
        usepots=False,
        description="Convert XLIFF localization files to Gettext PO localization files."
    )
    parser.add_duplicates_option()
    parser.run(['--errorlevel=exception', xliff, locale])
    return 0


def _pocompile(locale):
    formats = {"po": ("mo", convertmo)}
    parser = convert.ConvertOptionParser(
        formats,
        usepots=False,
        description="Compile Gettext PO localization files into Gettext MO (Machine Object) files."
    )
    parser.add_fuzzy_option()
    parser.run(['--fuzzy', '--errorlevel=exception', locale, locale])
    return 0


def make(inp=None, out=None, condensed=True):
    if inp is None:
        files = fnmatch.filter(os.listdir('.'), core.EXT_LIBRARY)
        if files:
            inp = files[0]

    if inp and os.path.isdir(inp):
        po = xlf = False
        exti = exto = ''
        for dirpath, dirnames, filenames in os.walk(inp):
            files = fnmatch.filter(filenames, '*.po')
            po = bool(files)
            files = fnmatch.filter(filenames, '*.xlf')
            xlf = bool(files)
            if po or xlf:
                break
        exti = 'po' if po else 'xlf' if xlf else ''
        if not exti:
            raise MakeError('Not able to find *.po or *.xlf input files')

        inp = os.path.abspath(inp)
        if out is None and exti == 'po':
            return _pocompile(inp)

        if out:
            out = os.path.abspath(out)
            if os.path.isdir(out):
                for dirpath, dirnames, filenames in os.walk(out):
                    files = fnmatch.filter(filenames, '*.po')
                    po = bool(files)
                    files = fnmatch.filter(filenames, '*.xlf')
                    xlf = bool(files)
                    if po or xlf:
                        break
                exto = 'po' if po else 'xlf' if xlf else ''
                if exti == exto:
                    raise MakeError('Not able to handle the transition from *.{exti} to *.{exto}'.format(exti=exti, exto=exto))
            else:
                os.mkdir(out)
                exto = 'xlf'
            return {('po', 'xlf'): _po2xliff, ('xlf', 'po'): _xliff2po}[(exti, exto)](inp, out)

    if inp is None or not os.path.isfile(inp):
        raise MakeError('Not able to find input file')
    out_name, exti = os.path.splitext(inp)
    exti = exti[1:]
    if exti not in INPUT_EXT:
        raise MakeError('Not able to handle file format: *.{ext}'.format(ext=exti))
    inp = os.path.abspath(inp)

    if out is None:
        out = "{0}.{1}".format(os.path.splitext(os.path.basename(inp))[0], 'chm')
    name, exto = os.path.splitext(out)
    exto = exto[1:]
    if not exto:
        exto = os.path.basename(name)

    if exto not in OUTPUT_EXT:
        raise MakeError('Not able to handle file format: *.{ext}'.format(ext=exto))
    out = os.path.abspath(out)

    if (exti, exto) not in TRANSITIONS:
        raise MakeError('Not able to handle the transition from *.{exti} to *.{exto}'.format(exti=exti, exto=exto))

    if exto == 'html':
        out = os.path.join(os.path.dirname(out), "{0}-html".format(out_name))

    _before_export = _after_export = None
    _before_clean = _after_clean = None
    _before_generate = _after_generate = None
    _before_transform = _after_transform = None

    conf = core.get_configuration()
    if conf and "Hooks" in conf:
        hooks = conf["Hooks"]
        _before_export = get_hook(hooks, "BeforeExport")
        _after_export = get_hook(hooks, "AfterExport")
        _before_clean = get_hook(hooks, "BeforeClean")
        _after_clean = get_hook(hooks, "AfterClean")
        _before_generate = get_hook(hooks, "BeforeGenerate")
        _after_generate = get_hook(hooks, "AfterGenerate")
        _before_transform = get_hook(hooks, "BeforeTransform")
        _after_transform = get_hook(hooks, "AfterTransform")

    if exti == 'library':
        core.exec_hook(_before_export, [inp])
        content = _export(inp)
        inp = content
        core.exec_hook(_after_export, [content])

    core.exec_hook(_before_clean, [inp])
    content = _clean(inp)
    core.exec_hook(_after_clean, [content])

    core.exec_hook(_before_generate, [content, condensed])
    frame = _generate(content, condensed=condensed)
    core.exec_hook(_after_generate, [frame])

    core.exec_hook(_before_transform, [exto, frame, out])
    product = _transform(exto, frame, out)
    core.exec_hook(_after_transform, [product])

    return 1 if product is None else 0


def get_hook(hooks, key):
    if key in hooks:
        target_file_path = hooks[key]
        if not os.path.isfile(target_file_path):
            raise MakeError('{0} hook target script file not found: {1}'.format(key, target_file_path))
        return target_file_path
    return None

