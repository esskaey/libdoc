# -*- coding: utf-8 -*-

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

import ctypes
import os
import sys

from . import core


class HtmlSvgConverter(object):

    def __init__(self):
        self._init_ok = 0

        basedir = core.get_base_dir()

        self.wkdll = ctypes.WinDLL(os.path.join(os.path.abspath(basedir), core.BINARIES, 'wkhtmltox.dll'))

        self.wkhtmltoimage_init = self.wkdll.wkhtmltoimage_init
        self.wkhtmltoimage_init.restype = ctypes.c_int
        self.wkhtmltoimage_init.argtypes = [ctypes.c_int]

        self.wkhtmltoimage_deinit = self.wkdll.wkhtmltoimage_deinit
        self.wkhtmltoimage_deinit.restype = ctypes.c_int

        self.wkhtmltoimage_create_global_settings = self.wkdll.wkhtmltoimage_create_global_settings
        self.wkhtmltoimage_init.restype = ctypes.c_void_p

        self.wkhtmltoimage_set_global_setting = self.wkdll.wkhtmltoimage_set_global_setting
        self.wkhtmltoimage_set_global_setting.restype = ctypes.c_int
        self.wkhtmltoimage_set_global_setting.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]

        self.wkhtmltoimage_get_global_setting = self.wkdll.wkhtmltoimage_get_global_setting
        self.wkhtmltoimage_get_global_setting.restype = ctypes.c_int
        self.wkhtmltoimage_get_global_setting.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]

        self.wkhtmltoimage_create_converter = self.wkdll.wkhtmltoimage_create_converter
        self.wkhtmltoimage_create_converter.restype = ctypes.c_void_p
        self.wkhtmltoimage_create_converter.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

        self.wkhtmltoimage_destroy_converter = self.wkdll.wkhtmltoimage_destroy_converter
        self.wkhtmltoimage_destroy_converter.argtypes = [ctypes.c_void_p]

        self.wkhtmltoimage_convert = self.wkdll.wkhtmltoimage_convert
        self.wkhtmltoimage_convert.restype = ctypes.c_int
        self.wkhtmltoimage_convert.argtypes = [ctypes.c_void_p]

    def __enter__(self):
        self._init_ok = self.wkhtmltoimage_init(0)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._init_ok:
            self.wkhtmltoimage_deinit()

    def html_to_svg(self, html, svg, width="320"):
        assert isinstance(html, unicode)
        assert isinstance(svg, unicode)
        assert isinstance(width, unicode)
        gs = self.wkhtmltoimage_create_global_settings()
        ret = self.wkhtmltoimage_set_global_setting(gs, "screenWidth", width)
        ret = self.wkhtmltoimage_set_global_setting(gs, "fmt", "svg")
        ret = self.wkhtmltoimage_set_global_setting(gs, "in", html)
        ret = self.wkhtmltoimage_set_global_setting(gs, "out", svg)
        converter = self.wkhtmltoimage_create_converter(gs, None)
        ret = self.wkhtmltoimage_convert(converter)
        self.wkhtmltoimage_destroy_converter(converter)
        return ret


class HtmlPdfConverter(object):
    def __init__(self):
        self._init_ok = 0

        basedir = core.get_base_dir()
        self.wkdll = ctypes.WinDLL(os.path.join(os.path.abspath(basedir), core.BINARIES, 'wkhtmltox.dll'))

        self.wkhtmltopdf_init = self.wkdll.wkhtmltopdf_init
        self.wkhtmltopdf_init.restype = ctypes.c_int
        self.wkhtmltopdf_init.argtypes = [ctypes.c_int]

        self.wkhtmltopdf_deinit = self.wkdll.wkhtmltopdf_deinit
        self.wkhtmltopdf_deinit.restype = ctypes.c_int

        self.wkhtmltopdf_create_global_settings = self.wkdll.wkhtmltopdf_create_global_settings
        self.wkhtmltopdf_init.restype = ctypes.c_void_p

        self.wkhtmltopdf_set_global_setting = self.wkdll.wkhtmltopdf_set_global_setting
        self.wkhtmltopdf_set_global_setting.restype = ctypes.c_int
        self.wkhtmltopdf_set_global_setting.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]

        self.wkhtmltopdf_create_converter = self.wkdll.wkhtmltopdf_create_converter
        self.wkhtmltopdf_create_converter.restype = ctypes.c_void_p
        self.wkhtmltopdf_create_converter.argtypes = [ctypes.c_void_p]

        self.wkhtmltopdf_create_object_settings = self.wkdll.wkhtmltopdf_create_object_settings
        self.wkhtmltopdf_init.restype = ctypes.c_void_p

        self.wkhtmltopdf_set_object_setting = self.wkdll.wkhtmltopdf_set_object_setting
        self.wkhtmltopdf_set_object_setting.restype = ctypes.c_int
        self.wkhtmltopdf_set_object_setting.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]

        self.wkhtmltopdf_add_object = self.wkdll.wkhtmltopdf_add_object
        self.wkhtmltopdf_add_object.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]

        self.wkhtmltopdf_convert = self.wkdll.wkhtmltopdf_convert
        self.wkhtmltopdf_convert.restype = ctypes.c_int
        self.wkhtmltopdf_convert.argtypes = [ctypes.c_void_p]

        self.wkhtmltopdf_destroy_converter = self.wkdll.wkhtmltopdf_destroy_converter
        self.wkhtmltopdf_destroy_converter.argtypes = [ctypes.c_void_p]

        self.wkhtmltopdf_set_error_callback = self.wkdll.wkhtmltopdf_set_error_callback
        self.wkhtmltopdf_set_error_callback.argtypes = [ctypes.c_void_p, ctypes.c_void_p]

        self.wkhtmltopdf_str_callback = ctypes.CFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_char_p)

    def __enter__(self):
        self._init_ok = self.wkhtmltopdf_init(0)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._init_ok:
            self.wkhtmltopdf_deinit()

    def html_to_pdf(self, html_file, pdf_file, doc_title, copyright, title_page_html_file, toc_xsl_file):
        assert isinstance(pdf_file, unicode)
        assert isinstance(doc_title, unicode)
        assert isinstance(title_page_html_file, unicode)

        global_settings = self.wkhtmltopdf_create_global_settings()
        ret = self.wkhtmltopdf_set_global_setting(global_settings, 'size.width', '21cm')
        ret = self.wkhtmltopdf_set_global_setting(global_settings, 'size.height', '29.7cm')
        ret = self.wkhtmltopdf_set_global_setting(global_settings, 'orientation', 'Portrait')
        ret = self.wkhtmltopdf_set_global_setting(global_settings, 'colorMode', 'Color')
        ret = self.wkhtmltopdf_set_global_setting(global_settings, 'outline', 'false')
        ret = self.wkhtmltopdf_set_global_setting(global_settings, 'out', pdf_file)
        ret = self.wkhtmltopdf_set_global_setting(global_settings, 'documentTitle', doc_title)
        ret = self.wkhtmltopdf_set_global_setting(global_settings, 'margin.top', '2.5cm')
        ret = self.wkhtmltopdf_set_global_setting(global_settings, 'margin.bottom', '3cm')
        ret = self.wkhtmltopdf_set_global_setting(global_settings, 'margin.left', '2cm')
        ret = self.wkhtmltopdf_set_global_setting(global_settings, 'margin.right', '1.5cm')

        converter = self.wkhtmltopdf_create_converter(global_settings)
        # callback = self.wkhtmltopdf_str_callback(_html_to_pdf_error_callback)
        # self.wkhtmltopdf_set_error_callback(converter, callback)

        title_page_settings = self.wkhtmltopdf_create_object_settings()
        ret = self.wkhtmltopdf_set_object_setting(title_page_settings, 'page', title_page_html_file)
        self.wkhtmltopdf_add_object(converter, title_page_settings, 0)

        toc_settings = self.wkhtmltopdf_create_object_settings()
        ret = self.wkhtmltopdf_set_object_setting(toc_settings, 'isTableOfContent', 'true')
        ret = self.wkhtmltopdf_set_object_setting(toc_settings, 'toc.useDottedLines', 'true')
        ret = self.wkhtmltopdf_set_object_setting(toc_settings, 'toc.captionText', 'Contents')
        ret = self.wkhtmltopdf_set_object_setting(toc_settings, 'tocXsl', toc_xsl_file)
        self.wkhtmltopdf_add_object(converter, toc_settings, 0)

        content_settings = self.wkhtmltopdf_create_object_settings()
        ret = self.wkhtmltopdf_set_object_setting(content_settings, 'page', html_file)
        ret = self.wkhtmltopdf_set_object_setting(content_settings, 'header.left',
                                                  'CODESYS - Inspiring Automation Solutions')
        ret = self.wkhtmltopdf_set_object_setting(content_settings, 'header.right', doc_title)
        ret = self.wkhtmltopdf_set_object_setting(content_settings, 'header.fontSize', '8')
        ret = self.wkhtmltopdf_set_object_setting(content_settings, 'header.line', 'true')
        ret = self.wkhtmltopdf_set_object_setting(content_settings, 'header.spacing', '15')
        ret = self.wkhtmltopdf_set_object_setting(content_settings, 'footer.left', copyright)
        ret = self.wkhtmltopdf_set_object_setting(content_settings, 'footer.right', '[page] / [toPage]')
        ret = self.wkhtmltopdf_set_object_setting(content_settings, 'footer.fontSize', '8')
        ret = self.wkhtmltopdf_set_object_setting(content_settings, 'footer.line', 'true')
        ret = self.wkhtmltopdf_set_object_setting(content_settings, 'footer.spacing', '15')

        self.wkhtmltopdf_add_object(converter, content_settings, 0)

        ret = self.wkhtmltopdf_convert(converter)
        ret = self.wkhtmltopdf_destroy_converter(converter)


'''
def _html_to_pdf_error_callback(converter, message):
    pass
'''
