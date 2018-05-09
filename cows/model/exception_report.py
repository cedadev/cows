# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

# Copyright (C) 2007 STFC & NERC (Science and Technology Facilities Council).
# This software may be distributed under the terms of the
# Q Public License, version 1.0 or later.
# http://ndg.nerc.ac.uk/public_docs/QPublic_license.txt
"""
Classes modelling the OWS Exception Report package v1.1.0.

:author: Stephen Pascoe
"""

class ExceptionReport(object):
    """
    :ivar version:
    :type version: str
    :ivar lang:
    :type lang: None or str, from RFC 4646
    :ivar exceptions: Iterable of OWSException objects

    """
    def __init__(self, exceptions, version, lang=None):
        self.version = version
        self.exceptions = exceptions
        self.lang = lang

class OwsException(object):
    """
    :ivar code:
    :type code: str
    :ivar text:
    :type text: None or str
    :ivar locator:
    :type locator: None or str

    """
    def __init__(self, code, text=None, locator=None):
        self.code = code
        self.text = text
        self.locator = locator

class OwsError(Exception):
    """Wrapper for triggering ExceptionReports via raise.

    :todo: Design an elegant way of setting the version framework-wide.
    :ivar report: The ExceptionReport describing the error.
    
    """
    def __init__(self, code, text=None, locator=None, version='1.1.0', lang=None):
        self.report = ExceptionReport([OwsException(code, text, locator)], version, lang)

    def __str__(self):
        """A concise non-XML representation of the error
        """
        e = self.report.exceptions[0]
        return '%s: %s (%s)' % (e.code, e.text, e.locator)
