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
Standard OWS Common exceptions

@author: Stephen Pascoe
"""

from cows.model.exception_report import OwsError

class OperationNotSupported(OwsError):
    def __init__(self, text, locator=None):
        OwsError.__init__(self, 'OperationNotSupported', text, locator)

class MissingParameterValue(OwsError):
    def __init__(self, text, locator=None):
        OwsError.__init__(self, 'MissingParameterValue', text, locator)

class InvalidParameterValue(OwsError):
    def __init__(self, text, locator=None):
        OwsError.__init__(self, 'InvalidParameterValue', text, locator)

class VersionNegotiationFailed(OwsError):
    def __init__(self, text, locator=None):
        OwsError.__init__(self, 'VersionNegotiationFailed', text, locator)

class InvalidUpdateSequence(OwsError):
    def __init__(self, text, locator=None):
        OwsError.__init__(self, 'InvalidUpdateSequence', text, locator)

class CurrentUpdateSequence(OwsError):
    def __init__(self, text, locator=None):
        OwsError.__init__(self, 'CurrentUpdateSequence', text, locator)

class NoApplicableCode(OwsError):
    def __init__(self, text, locator=None):
        OwsError.__init__(self, 'NoApplicableCode', text, locator)

