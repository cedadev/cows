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
Classes modelling the OWSServiceMetadata portion of the OWS Get Capabilities package v1.1.0.

:author: Stephen Pascoe
"""

class ServiceMetadata(object):
    """
    :ivar serviceIdentification:
    :ivar serviceProvider:
    :ivar operationsMetadata:
    :ivar contents:

    """
    def __init__(self, serviceIdentification=None, serviceProvider=None,
                 operationsMetadata=None, contents=None):
        self.serviceIdentification = serviceIdentification
        self.serviceProvider = serviceProvider
        self.operationsMetadata = operationsMetadata
        self.contents = contents
        
