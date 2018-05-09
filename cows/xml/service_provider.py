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
Reads XML fragments from the OWS ServiceProvider package v1.1.0 and
creates cows objects.

Each function expects an ElementTree node as it's first argument and returns
an cows object.

@author: Stephen Pascoe
"""

from cows.xml import ns
from cows.xml.util import *
from cows.xml.iso19115_subset import *
from cows.model.service_provider import *

def service_provider(node):
    sp = ServiceProvider(
           providerName=find_text(node, './{%s}ProviderName' % ns.ows),
           serviceContact=find_with(node, './{%s}ServiceContact' % ns.ows,
                                     responsible_party),
           providerSite=find_with(node, './{%s}ProviderSite' % ns.ows,
                                   online_resource)
           )
    return sp
