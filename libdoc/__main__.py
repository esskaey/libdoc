#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CODESYS LibDoc Scripting Collection V{version}

Usage:
    libdoc -h | --help | --version
    libdoc export [<library> [<content>]]
    libdoc clean [<original-content> [<cleaned-content>]]
    libdoc generate [-f] [-b] [-c] [-s | --slug=<maxch>] [<content> [<frame>]]  
    libdoc merge [-d] [<content> [<frame> [<source>]]]
    libdoc transform ({formats}) [[<struct>] [<language>]]
    libdoc make [-n] [<input> [<output>]]
    libdoc fresh [<frame>]

Options:
    -h --help       Show this screen.
    --version       Show version.
    -s              Slugify (ensure readable) names for file names. The length of the name stems is limited to 16.
    --slug=<maxch>  Specify maximal length for slugified file name stems. 
    <library>       The CODESYS library.
    <content>       JSON serialized content of a CODESYS library.
    <frame>         Folder structure which mimics the structure of the library.
    <source>        The project folder for the sphinx-doc package.
    <struct>        One of the following structures: <frame> or <source>
    <language>      The code for the language in which the documentation will be localized.
    <input>         A file of one of the following types library, json
    <output>        A file or a folder of one of the following types chm, lmd, html

Commands:
    export          Using CODESYS and its DocExport functionality to serialize the <content> in a JSON file.
                    This command needs a CODESYS installation.

    clean           Analyses the <original-content> and generates a cleaned version named <cleaned-content>.
                    The default behaviour is defined as follows:
                    * Elements marked with the attributes ``hide`` and ``conditionalshow`` will be removed.
                    * Elements with the modifiers ``INTERNAL`` and ``PRIVATE`` will be removed.
                    * All other Elements will not be removed.
                    This default behaviour can be adapted individually by providing a customized ``clean.conf`` file.

    generate        Parse the library <content> and generates/updates the <frame> folder structure which mimics
                    the structure of the library.
                    The option '-f' forces overwriting existing files!
                    The option '-b' generates a *.bak file before overwriting an existing file.
                    The option '-c' generates condensed paths inside the <frame> (Only one folder level).
                    The options '-s' and '--slug' generates slugified filenames inside the <frame>. 
                    The later allows to specify the maximal number of character of file name stem.
                    Both options work only together with '-c' option.
                    Note: The file 'conf.py' will never be overwritten.

    merge           Replaces the placeholders in the <frame> structure and  generates/updates
                    a sphinx-doc project structure <source>. (The option '-d' displays the merge cache for debugging)

    transform       Using the sphinx-doc package to transform the <source> structure in a distributable
                    document in {format_text} format.
                    This command needs for generating a chm-file the installation of the Microsoft HTML-Workshop software.
                    The following formats are available:
{format_doc}

    make            Tries to generate the <output> from the defined <input>.
                    The option '-n' generates normal paths inside the <frame>.
                    Generating condensed paths is the default.
                    Examples:
                    libdoc make lib.library lib.lmd -> Generates a lib.lmd file from lib.library
                    libdoc make lib.json lib.lmd -> Generates a lib.lmd file from lib.json
                    libdoc make lib.library lib.chm -> Generates a lib.chm file from lib.library
                    libdoc make lib.json lib.chm -> Generates a lib.chm file from lib.json
                    libdoc make lib.library html -> Generates a lib-html folder from lib.library
                    libdoc make lib.json html -> Generates a lib-html folder from lib.json
                    libdoc make po-dir xlf-dir -> Convert the po files to XLIFF files
                    libdoc make xlf-dir po-dir -> Convert the XLIFF files to po files
                    libdoc make po-dir -> Convert the po files to mo files

    fresh           Tries to generate a fresh frame documentation folder structure in the current working directory.
                    The parameter <frame> is optional and defaults to "Frame".
"""
import multiprocessing
import sys

from docopt import docopt

from libdoc import __version__ as version
from libdoc.exceptions import LibDocError
from libdoc.transformer import builders, builder_docs
from libdoc.export import export
from libdoc.generate import generate
from libdoc.merge import merge
from libdoc.transform import transform
from libdoc.make import make
from libdoc.clean import clean
from libdoc.qstart import fresh


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    code = 0
    kwargs = {}
    argv = [arg for arg in argv]

    formats = sorted(builders)
    doc = __doc__.format(
        version=version,
        formats='|'.join(formats),
        format_text=', '.join(formats[:-1]) + ' or ' + formats[-1],
        format_doc=builder_docs(20)
    )
    arguments = docopt(doc, argv=argv, version=version)
    if arguments:
        if arguments['-f']:
            kwargs['force'] = True
        if arguments['-b']:
            kwargs['backup'] = True
        if arguments['-d']:
            kwargs['debug'] = True
        if arguments['-c']:
            kwargs['condensed'] = True
            if arguments['-s']:
                kwargs['slug'] = 16
            if arguments['--slug'] and arguments['--slug'].isnumeric():
                kwargs['slug'] = int(arguments['--slug'])
        if arguments['-n']:
            kwargs['condensed'] = False
        command = argv[0]
        argv = [arg for arg in argv[1:] if not arg.startswith('-')]
        commands = globals()  #: The imported symbols like export, generate, transform, ... are members of globals()
        if arguments[command] and command in commands:
            command = commands[command]
            print(doc.splitlines()[1])
            code = command(*argv, **kwargs)
    return code

if __name__ == '__main__':
    multiprocessing.freeze_support()
    try:
        sys.exit(main())
    except LibDocError as ex:
        print("{0}: {1}".format(type(ex).__name__, ex.message))
        sys.exit(1)
