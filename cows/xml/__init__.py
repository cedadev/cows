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
Reads XML fragments and creates cows objects.

This package is written in a functional rather than object orientated
style.  Each function expects an ElementTree node as it's first
argument and returns an cows object.

@author: Stephen Pascoe
"""

from cows.xml.service_identification import *
from cows.xml.service_provider import *
from cows.xml import ns
from cows.xml.util import *
from cows.model import ServiceMetadata

def service_metadata(node):
    sm = ServiceMetadata(
           serviceIdentification=find_with(node, './{%s}ServiceIdentification'
                                           % ns.ows, service_identification),
           serviceProvider=find_with(node, './{%s}ServiceProvider' % ns.ows,
                                     service_provider)
           )
    return sm
        
