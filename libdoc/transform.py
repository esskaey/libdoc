# -*- coding: utf-8 -*-
"""
    Transform
    ~~~~~~~~~

    Transforms the <source> documentation structure to different formats

    :html: Sphinx html builder
    :chm: Microsoft HTML Help format
    :lmd: CODESYS (l)ibrary (m)anager (d)ocumentation format
    :xml: Docutils native XML files
    :json: Produces a directory with JSON files
    :latex: Produces a bunch of LaTeX files, basis for pdf transformation
    :pot: Produces gettext-style message catalogs, basis for localisation

    ``sphinx-build -b htmlhelp`` will produce::

    <library-name>.hhc <- Content/Structure
    <library-name>.hhk <- Index/Keywords
    <library-name>.hhp <- Project settings
    <library-name>.stp <- Stop word list

    The \*.hhp -> \*.chm compiler is located at: ``C:\\Program Files (x86)\\HTML Help Workshop\\hhc.exe``

    For transformation, call: ``C:\\Program Files (x86)\\HTML Help Workshop\\hhc.exe" "<path>\\<library-name>.hhp``

    For ``*.chm`` we need to change the content of the ``*.hhc`` file.

    The original::

        <OBJECT type="text/site properties">
            <param name="Window Styles" value="0x801227">
            <param name="ImageType" value="Folder">
        </OBJECT>

    After the change::

        <OBJECT type="text/site properties">
            <param name="Window Styles" value="0x801227">
        </OBJECT>

    The Original::

        <UL>
            <LI> <OBJECT type="text/sitemap">
                    <param name="Name" value="CODESYS LibDevSummary V3.5.5.0 draft">
                    <param name="Local" value="index.html">
                </OBJECT>

            [...]

            <LI> <OBJECT type="text/sitemap">
                    <param name="Name" value="Introduction">
                    <param name="Local" value="introduction.html">
                </OBJECT>
        </UL>

    After the change::

        <UL>
            <LI> <OBJECT type="text/sitemap">
                    <param name="Name" value="CODESYS LibDevSummary V3.5.5.0 draft">
                    <param name="Local" value="index.html">
                </OBJECT>
            <UL>

            [...]

                <LI> <OBJECT type="text/sitemap">
                        <param name="Name" value="Introduction">
                        <param name="Local" value="introduction.html">
                    </OBJECT>
            </UL>
        </UL>
"""
import glob
import json
import os
import subprocess
import sys
import zipfile
import zlib
import fnmatch
import re
import io

from datetime import datetime
import importlib.util

import polib
from sphinx.cmd.build import build_main  # Update import

import unicodedata

from . import core
from .exceptions import HHCError, BuilderError, SourceError, LocalisationError
from .transformer import transformer, transformers, create_builder_state
from .wkhtmltox import HtmlSvgConverter, HtmlPdfConverter


def transform(builder='html', source=None, language=None):
    if source is None:
        files = fnmatch.filter(os.listdir('.'), core.SOURCE)
        if files:
            source = files[0]
            if not os.path.isdir(source):
                source = None

    if source is None or not os.path.isdir(source):
        raise SourceError('Not able to find the source structure')

    source = os.path.abspath(source)
    config = os.path.normpath(os.path.join(source, os.path.pardir))
    build = os.path.join(config, core.BUILD, os.path.basename(source))

    create_builder_state(config, builder, language)

    transformer_function = transformers.get(builder)
    if transformer_function is None:
        raise BuilderError(f'The {builder} format is not supported')
    else:
        return transformer_function(config, build, source, language)


@transformer('chm', 'Transforms the content of <source> to a compiled Microsoft HTML Help document.')
def make_chm(config, build, source, language=None):
    code = build_hhp(config, build, source, language)
    if code != 0:
        return code
    conf = core.read_conf(config)
    basename = conf.get('htmlhelp_basename', 'libdoc')
    chm_path = os.path.join(build, 'chm')
    if language is not None:
        chm_path = os.path.join(chm_path, language)
    hhp = os.path.join(chm_path, '{basename}.hhp'.format(basename=basename))
    hhc = os.path.join(chm_path, '{basename}.hhc'.format(basename=basename))
    chm = os.path.join(chm_path, '{basename}.chm'.format(basename=basename))
    hhp_age = os.path.getmtime(hhp) if os.path.isfile(hhp) else 0
    chm_age = os.path.getmtime(chm) if os.path.isfile(chm) else 0
    if hhp_age > chm_age:
        fix_hhc(hhc)
        code = compile_hhp(hhp)
    else:
        code = 0
    return code


def build_hhp(config, build, source, language=None):
    doctrees = os.path.join(build, 'doctrees')
    destination = os.path.join(build, 'chm')
    if language is not None:
        destination = os.path.join(destination, language)
    code = build_main(['sphinx-build',
                                '-b', 'htmlhelp',
                                '-c', config,  # The directory with conf.py,
                                '-d', doctrees,
                                '-t', 'libdoc_chm',
                                '-D', 'language={}'.format(language or 'en'),
                                source,  # Source file directory
                                destination  # Destination directory
                                ])
    return code


def fix_hhc(hhc):
    """
    For using the ``*.chm`` in a CODESYS online help system we need to tweak the ``*.hhc``

        * We want to use "book" icons and not "folder" icons.
        * Only the first topic should be at the first level of the TOC.
          All other topics should show as deeper nested topics.

    | The issue will be fixed by the removal of the ``ImageType`` property inside the ``text/site properties`` element.
    | The second issue will be fixed by injecting a additional ``<UL></UL>`` wrapper after the top level topic element.
      This will place the other topics in a additional TOC level.
    """
    state = 0
    output = io.StringIO()
    with open(hhc, "r", encoding='iso-8859-1') as f:
        for line in f:
            line = line.rstrip()
            if state == 0 and '<OBJECT type="text/site properties">' in line:
                state = 1
            elif state == 1 and 'LibDoc -->' in line:
                # This file is already fixed
                return
            elif state == 1 and '<param name="ImageType" value="Folder">' in line:
                state = 2
                # We want Book not Folders in the \*.chm file
                line = line.replace(
                    '<param name="ImageType" value="Folder">', '<!-- param name="ImageType" value="Folder" LibDoc -->')
            elif state == 2 and '<OBJECT type="text/sitemap">' in line:
                state = 3
            elif state == 3 and '</OBJECT>' in line:
                line += '\n<UL> <!-- LibDoc -->'
                state = 4
            elif state == 4 and '</UL></BODY></HTML>' in line:
                line = '</UL> <!-- LibDoc -->\n' + line
                state = 99
            print(line, file=output)
    with open(hhc, 'w', encoding='iso-8859-1') as f:
        f.write(output.getvalue())


def compile_hhp(hhp):
    hhp = os.path.abspath(hhp)
    if not os.path.isfile(hhp):
        raise HHCError("Not able to find project file")
    chm = None
    with open(hhp, 'r', encoding='iso-8859-1') as f:
        for line in f:
            if 'Compiled file=' not in line:
                continue
            index = line.find('=')
            chm = line[index + 1:].rstrip()
            break
    if chm is None:
        raise HHCError("Not able to find *.chm file")
    chm = os.path.abspath(os.path.join(os.path.dirname(hhp), chm))
    compiler = os.environ.get(core.LIBDOC_HHC)
    if compiler is None:
        root = os.environ.get(core.PROGRAMFILES)
        if root is None:
            raise HHCError("Not able to find program files folder")
        compiler = os.path.join(root, *core.HHC_EXE_PATH)
    if not os.path.isfile(compiler):
        raise HHCError('Not able to find a HHC.EXE')
    cmd = '"{hhc}" "{hhp}"'.format(hhc=compiler, hhp=hhp)
    print("Transform <hhp> to <chm> using <hhc>")
    print("<hhp> =", hhp)
    print("<chm> =", chm)
    print("<hhc> =", compiler)
    print("calling:", cmd)
    print("...")
    code = subprocess.call(cmd)
    if code == 1:
        # Microsoft HTML Workshop return 1 if the run was successful
        # So we set it to 0. This means successful for the Python environment
        code = 0
    print("Result:", code, "-- Done!")
    return code


@transformer('html', 'Transforms the content of <source> to a collection of static html pages.')
def make_html(config, build, source, language=None):
    doctrees = os.path.join(build, 'doctrees')
    if language is None:
        destination = os.path.join(build, 'html')
    else:
        destination = os.path.join(build, 'html', language)
    code = build_main(['sphinx-build',
                                '-b', 'html',
                                '-c', config,  # The directory with conf.py,
                                '-d', doctrees,
                                '-t', 'libdoc_html',
                                '-D', "language={}".format(language or 'en'),
                                source,  # Source directory
                                destination,  # Destination directory
                                ])
    return code


@transformer('pdf', 'Transforms the content of <source> to a document in pdf format.')
def make_pdf(config, build, source, language=None):
    doctrees = os.path.join(build, 'doctrees')
    if language is None:
        source_dir = os.path.join(build, 'pdf', 'html')
        destination_dir = os.path.join(build, 'pdf')
    else:
        source_dir = os.path.join(build, 'pdf', language, 'html')
        destination_dir = os.path.join(build, 'pdf', 'language')
    code = build_main(['sphinx-build',
                                '-b', 'singlehtml',
                                '-c', config,  # The directory with conf.py
                                '-d', doctrees,
                                '-t', 'libdoc_html',
                                '-D', 'language={}'.format(language or 'en'),
                                source,  # Source directory (Frame)
                                source_dir,  # Destination directory (which is the source for the subsequent pdf step)
                                ])
    if code:
        return code

    conf_py_file = os.path.join(config, 'conf.py')
    conf_module = importlib.util.spec_from_file_location('conf', conf_py_file)
    cover_html_file = os.path.join(config, 'Theme', 'pdf', 'static', 'cover.html')
    cover_dest_html_file = os.path.join(source_dir, 'cover.html')
    toc_xsl_file = os.path.join(config, 'Theme', 'pdf', 'static', 'toc.xsl')
    html_file = os.path.join(source_dir, 'index.html')
    pdf_file = os.path.join(destination_dir, pdf_name_from_project(conf_module.project) + '.pdf')

    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # Create a temporary cover.html file which reflects the document variables
    with open(cover_html_file, 'r',encoding="utf-8") as f_cover_html:
        cover_html = f_cover_html.read()
    cover_html = cover_html.replace('[title]', conf_module.project)
    cover_html = cover_html.replace('[copyright]', conf_module.copyright)
    cover_html = cover_html.replace('[version]', conf_module.version)
    cover_html = cover_html.replace('[subtitle]', '')   # TODO
    with open(cover_dest_html_file, 'w',encoding="utf-8") as f_cover_temp_html:
        f_cover_temp_html.write(cover_html)

    with HtmlPdfConverter() as converter:
        converter.html_to_pdf(html_file, pdf_file, conf_module.project, conf_module.copyright, cover_dest_html_file,
                              toc_xsl_file)

    return 0


def pdf_name_from_project(project):
    value = project
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    value = re.sub('[-\s]+', '-', value)
    return value


@transformer('pot', 'Transforms the content of <source> to a gettext-style message catalog, basis for localisation.')
def make_pot(config, build, source, language=None):
    if language is not None:
        language = None

    doctrees = os.path.join(build, 'pottrees')
    code = build_main(['sphinx-build',
                                '-b', 'gettext',
                                '-c', config,  # The directory with conf.py,
                                '-d', doctrees,
                                '-t', 'libdoc_pot',
                                source,  # Source directory
                                os.path.join(build, 'pot'),  # Destination directory
                                ])

    pot_dir = os.path.join(build, 'pot')
    conf = core.read_conf(config)
    locale_dirs = conf.get('locale_dirs', [core.LOCALE_DIR])
    for locale_dir in locale_dirs:
        update_pot(os.path.join(source, locale_dir), pot_dir)
    return code


def update_pot(locale_dir, pot_dir, languages=None):

    if not os.path.exists(pot_dir):
        raise LocalisationError("Not able to find the *.pot file folder: '{}'".format(pot_dir))
    if languages is None:
        languages = [os.path.relpath(d, locale_dir)
                     for d in glob.glob(os.path.join(locale_dir, '[a-z]*'))
                     if os.path.isdir(d) and not d.endswith('pot')]
    if not languages:
        languages = os.environ.get(core.LIBDOC_LOCALISATION)
        if languages is not None:
            languages = [s.strip() for s in languages.split(',')]
    if languages is None:
        languages = core.LOCALISATION_LIST

    for dirpath, dirnames, filenames in os.walk(pot_dir):
        for filename in filenames:
            pot_file = os.path.join(dirpath, filename)
            base, ext = os.path.splitext(pot_file)
            if ext != ".pot":
                continue
            basename = os.path.relpath(base, pot_dir)
            for lang in languages:
                po_dir = os.path.join(locale_dir, lang, 'LC_MESSAGES')
                po_file = os.path.join(po_dir, basename + ".po")
                out_dir = os.path.dirname(po_file)
                if not os.path.exists(out_dir):
                    os.makedirs(out_dir)

                pot = polib.pofile(pot_file)
                if os.path.exists(po_file):
                    po = polib.pofile(po_file)
                    msg_ids = set([str(m) for m in po])
                    po.merge(pot)
                    new_msg_ids = set([str(m) for m in po])
                    if msg_ids != new_msg_ids:
                        added = new_msg_ids - msg_ids
                        deleted = msg_ids - new_msg_ids
                        print('Update:', po_file, "+%d, -%d" % (
                            len(added), len(deleted)))
                        po.save(po_file)
                    else:
                        print('Not Changed:', po_file)
                else:
                    po = polib.POFile()
                    po.metadata = pot.metadata
                    print('Create:', po_file)
                    po.merge(pot)
                    po.save(po_file)


@transformer('latex', 'Transforms the content of <source> to a bunch of LaTeX files, basis for pdf transformation.')
def make_latex(config, build, source, language=None):
    doctrees = os.path.join(build, 'doctrees')
    destination = os.path.join(build, 'latex')
    if language is not None:
        destination = os.path.join(destination, language)
    code = build_main(['sphinx-build',
                                '-b', 'latex',
                                '-c', config,  # The directory with conf.py,
                                '-d', doctrees,
                                '-t', 'libdoc_tex',
                                '-D', "language={}".format(language or 'en'),
                                source,  # Source directory
                                destination,  # Destination directory
                                ])
    return code


@transformer('json', 'Transforms the content of <source> to a directory with JSON files.')
def make_json(config, build, source, language=None):
    doctrees = os.path.join(build, 'doctrees')
    destination = os.path.join(build, 'json')
    if language is not None:
        destination = os.path.join(destination, language)
    code = build_main(['sphinx-build',
                                '-b', 'json',
                                '-c', config,  # The directory with conf.py,
                                '-d', doctrees,
                                '-t', 'libdoc_json',
                                '-D', "language={}".format(language or 'en'),
                                source,  # Source directory
                                destination,  # Destination directory
                                ])
    return code


@transformer('xml', 'Transforms the content of <source> to the Docutils native XML files.')
def make_xml(config, build, source, language=None):
    doctrees = os.path.join(build, 'doctrees')
    destination = os.path.join(build, 'xml')
    if language is not None:
        destination = os.path.join(destination, language)
    code = build_main(['sphinx-build',
                                '-b', 'xml',
                                '-c', config,  # The directory with conf.py,
                                '-d', doctrees,
                                '-t', 'libdoc_xml',
                                '-D', "language={}".format(language or 'en'),
                                source,  # Source directory
                                destination,  # Destination directory
                                ])
    return code


@transformer('lmd', 'Transforms the content of <source> to a CODESYS compatible library manager documentation element.')
def make_lmd(config, build, source, language=None):
    doctrees = os.path.join(build, 'doctrees')
    lmd_folder = os.path.join(build, 'lmd')
    destination = lmd_folder
    if language is not None:
        destination = os.path.join(lmd_folder, language)
    code = build_main(['sphinx-build',
                                '-b', 'html',
                                '-c', config,  # The directory with conf.py,
                                '-d', doctrees,
                                '-t', 'libdoc_lmd',
                                '-D', "language={}".format(language or 'en'),
                                source,  # Source directory
                                destination,  # Destination directory
                                ])
    if code != 0:
        return code

    try:
        # read the frame information file to get title, version and company of the related library
        with open(os.path.join(source, 'frame.json'), 'r', encoding='utf-8') as f:
            print('reading frame info ...', end="")
            frame_data = json.load(f)
    except IOError:
        frame_data = None

    if frame_data is None:
        return 1
    print (" done")
    inventory_file = os.path.join(destination, 'objects.inv')
    lib_data = frame_data['library']
    lmd_file = "{0}.{1}".format(os.path.splitext(lib_data['file'])[0], 'lmd')
    lmd_path = os.path.join(destination, lmd_file)
    inventory_age = os.path.getmtime(inventory_file)
    lmd_age = os.path.getmtime(lmd_path) if os.path.isfile(lmd_path) else 0

    if inventory_age <= lmd_age:
        print(lmd_file, 'is not out of date.')
        return 0

    if 'extensions' in frame_data and 'kinematics' in frame_data['extensions']:
        print("transforming kinematics...", end="")
        kinematics = frame_data['extensions']['kinematics']['data'][0]
        trouble_count = 0
        build_path = os.path.join(build, 'lmd')
        if language is not None:
            build_path = os.path.join(build_path, language)
        with HtmlSvgConverter() as converter:
            for kinematic in kinematics.itervalues():
                width = "640"  # The header has a two column width
                for part in kinematic:
                    src = os.path.join(build_path, os.path.normpath(part['location']))
                    dst = os.path.join(build_path, os.path.normpath(part['image']))
                    code = converter.html_to_svg(src, dst, width)
                    width = "320"  # parameters has a one column width
                    if code != 1:
                        if trouble_count == 0:
                            print('\n')
                        print('Warning: Trouble with transforming "{0}"'.format(src))
                        trouble_count += 1
        if trouble_count > 0:
            print('transforming kinematics done. Troubles: {0}'.format(trouble_count))
        else:
            print(' done')

    data = read_inventory(inventory_file)
    if not data:
        return 1

    # generate a manifest file in JSON format
    data = {'header': {'name': core.MANIFEST_JSON,
                       'version': '0.0.0.4',
                       'created': datetime.utcnow().replace(microsecond=0).isoformat()},
            'library': {'title': lib_data['title'], 'version': lib_data['version'], 'company': lib_data['company']},
            'inventory': data}
    mapping = frame_data.get('mapping')
    if mapping:
        data.update({'mapping': mapping})
    extensions = frame_data.get('extensions')
    if extensions is not None:
        data.update({'extensions': extensions})
    print('generate {} ...'.format(core.MANIFEST_JSON), end="")
    with open(os.path.join(destination, core.MANIFEST_JSON), 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, sort_keys=True, separators=(',', ': '), ensure_ascii=False)
    print(" done")

    # collect all necessary files and put these files in a zip archive
    # http://stackoverflow.com/questions/1855095/how-to-create-a-zip-archive-of-a-directory-in-python
    with zipfile.ZipFile(lmd_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        print('generate', lmd_file, '...', end="")
        for root, dirs, files in os.walk(destination):
            # add directory (needed for empty dirs)
            zip_file.write(root, os.path.relpath(root, destination))
            if "_sources" in dirs:
                dirs.remove("_sources")
            for f in files:
                if f in [lmd_file, "search.html", "searchindex.js", "todo.html", "genindex.html", ".buildinfo"]:
                    continue
                file_name = os.path.join(root, f)
                if os.path.isfile(file_name):  # regular files only
                    relative_file_name = os.path.join(os.path.relpath(root, destination), f)
                    zip_file.write(file_name, relative_file_name)
        print(' done')
    return code


def read_inventory(inv_file):

    data = {}
    with open(inv_file, 'rb') as f:
        line = f.readline()
        inv_format = line.rstrip().decode('utf-8')
        line = f.readline()
        title = line.rstrip()[11:].decode('utf-8')
        line = f.readline().decode()
        version = line.rstrip()[11:].decode('utf-8')
        line = f.readline().decode('utf-8')
        if 'zlib' not in line:
            raise ValueError

        def read_chunks():
            decompressor = zlib.decompressobj()
            for chunk in iter(lambda: f.read(16 * 1024), ''):
                yield decompressor.decompress(chunk)
            yield decompressor.flush()

        def split_lines(iterator):
            buf = ''
            for chunk in iterator:
                buf += chunk
                line_end = buf.find('\n')
                while line_end != -1:
                    yield buf[:line_end].decode('utf-8')
                    buf = buf[line_end + 1:]
                    line_end = buf.find('\n')
            assert not buf

        print('reading', inv_format[2:], 'for', title, version, '...', end="")
        for line in split_lines(read_chunks()):
            # be careful to handle names with embedded spaces correctly
            m = re.match(r'(?x)(.+?)\s+(\S*:\S*)\s+(\S+)\s+(\S+)\s+(.*)',
                         line.rstrip())
            if not m:
                continue
            name, entry_type, __, location, display_name = m.groups()
            if location.endswith(u'$'):
                location = location[:-1] + name
            location = os.path.join('.', location)
            data.setdefault(entry_type, {})[name] = {'location': location.replace('\\', '/').replace('./', ''),
                                                     'name': display_name}
        print(' done')
    return data
