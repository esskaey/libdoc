# -*- coding: utf-8 -*-
"""
    LibDoc
    ~~~~~~

    The CODESYS library documentation scripting collection

    :copyright: Copyright 2013-2016 by 3S-Smart Software Solutions GmbH.
    :license: see LICENSE for details.
"""

# version info for better programmatic use
# possible values for 3rd element: 'alpha', 'beta', 'tc', 'rc', 'final'
# 'final' has 0 as the last element
version_info = (3, 5, 13, 0, 'final', 0)
if version_info[4] == "final":
    __version__ = "{v[0]}.{v[1]}.{v[2]}.{v[3]}".format(v=version_info)
else:
    __version__ = "{v[0]}.{v[1]}.{v[2]}.{v[3]}{a}{v[5]}".format(
        v=version_info,
        a=version_info[4][0] if version_info[4] in ["alpha", "beta"] else version_info[4])
