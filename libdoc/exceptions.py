# -*- coding: utf-8 -*-
"""
Global LibDoc exception and warning classes.
"""


class LibDocError(Exception):
    pass


class LibraryError(LibDocError):
    pass


class ContentError(LibDocError):
    pass


class CodesysError(LibDocError):
    pass


class FrameError(LibDocError):
    pass


class SourceError(LibDocError):
    pass


class HHCError(LibDocError):
    pass


class BuilderError(LibDocError):
    pass


class MergeError(LibDocError):
    pass


class MergeCacheError(LibDocError):
    pass


class MakeError(LibDocError):
    pass


class JobListError(LibDocError):
    pass


class LocalisationError(LibDocError):
    pass