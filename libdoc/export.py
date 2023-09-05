# -*- coding: utf-8 -*-
"""
Export
~~~~~~

This module provides functionality for exporting the content out of a CODESYS library
"""

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
import sys
import os
import re
import subprocess
import fnmatch
from collections import namedtuple

from . import core
from .exceptions import CodesysError, LibraryError, ContentError, LibDocError


def export(library=None, content=None, root=None, filter=None):
    """
        | If ``config.json`` in ``Bin`` folder exist, it is used to find the host application.
        | Otherwise, the environment variable ``os.environ['LIBDOC_CODESYS']`` is used.
        | If variable not set, we try to find the latest CODESYS Version and use it for the export.
        | If library is None, we try to use the first library file in the current working directory
        | If content is None, we try to set it to ``./<library>.json``
    """
    host = None

    # Looking for host application with LibDoc Plug-in
    # Method 1: get info from a configuration file about host application, if exists
    # Method 2: get info from an environment variable LIBDOC_CODESYS
    # Method 3: look for installed CODESYS with highest version

    try:
        conf = core.get_configuration()
    except LibDocError:
        conf = None
        pass

    if conf:
        if "Host" in conf:
            host_config = conf["Host"]
            if "Path" in host_config:
                host = host_config["Path"]
                if "Params" in host_config:
                    params = host_config["Params"]
                    host = ' '.join([host, ' '.join(params)])

    if host is None:
        host = os.environ.get(core.LIBDOC_CODESYS)

    if host is None:
        latest_codesys = get_latest_codesys(root, filter)
        if latest_codesys is None:
            raise CodesysError('Not able to find a CODESYS.EXE')
        host = '"{codesys.exe}" --Profile="{codesys.profile}"'.format(codesys=latest_codesys)

    if library is None:
        files = fnmatch.filter(os.listdir('.'), core.EXT_LIBRARY)
        if files:
            library = files[0]
    if library is None or not os.path.isfile(library) or not fnmatch.fnmatch(library, core.EXT_LIBRARY):
        raise LibraryError('Not able to find a library file')
    library = os.path.abspath(library)

    if content is None:
        name = '{0}{1}'.format(os.path.splitext(os.path.basename(library))[0], os.path.splitext(core.EXT_JSON)[1])
        content = os.path.join(os.path.dirname(library), name)
    content = os.path.abspath(content)
    if not fnmatch.fnmatch(content, core.EXT_JSON):
        raise ContentError('Not able to create a content file')

    content_file = content
    cmd = '{exe} --noUI --skipunlicensedplugins --docexport="{lib}|{cnt}"'.format(exe=host, lib=library, cnt=content_file)
    print("Export <lib> to <content> using <codesys>")
    print("<lib> =", library)
    print("<content> =", content)
    print("<codesys> =", host)
    print("calling:", cmd)
    print("...")
    sys.stdout.flush()
    code = subprocess.call(cmd, stdout=sys.stdout, stderr=sys.stdout)
    sys.stdout.flush()
    msg = "-- Done!"
    if code != 2 and not os.path.isfile(content_file):
        code = 1  # no JSON file created !
        msg = "-- Error!"
    elif code == 2:
        msg = "-- The library is already in use, please close the other CODESYS instances!"
    print("Result:", code, msg)
    return code

Codesys = namedtuple('Codesys', ['version', 'exe', 'profile'])
"""
    A data structure to manage a concrete CODESYS exe
    The return data type of :func:`get_latest_codesys`
"""


def get_latest_codesys(root=None, filter=None):
    """ Try to find the latest CODESYS.EXE

        :param str root: The path for program files (like: ``C:\Program Files (x86)``)
        :param str filter: The pattern for CODESYS folder inside the program folder (like: ``3S CODESYS*``)
        :return: A :class:`Codesys` object or ``None``
    """
    if root is None:
        root = os.environ.get(core.PROGRAMFILES)
        if root is None:
            return None
    if filter is None:
        filter = core.CODESYS_FILTER

    codesys = None
    cur_version = ''
    dirs = fnmatch.filter(os.listdir(root), filter)
    for dir in dirs:
        path = os.path.join(root, dir, *core.PROFILE_PATH)
        if not os.path.isdir(path):
            continue
        exe = os.path.join(root, dir, *core.CODESYS_EXE_PATH)
        if not os.path.isfile(exe):
            continue
        files = fnmatch.filter(os.listdir(path), core.PROFILE_FILTER)
        for file in files:
            match = re.match(core.CDS_PROFILE_REGEX, file)
            if match is None:
                continue
            vg = match.groupdict(0)
            version = "{0:d}{1:d}{2:02d}{3:03d}".format(
                int(vg['main']), int(vg['minor']), int(vg['sp']), int(vg['patch']) * 10 + int(vg['hotfix']))
            if version > cur_version:
                cur_version = version
                profile = os.path.splitext(file)[0]
                codesys = Codesys(version, exe, profile)
    return codesys
