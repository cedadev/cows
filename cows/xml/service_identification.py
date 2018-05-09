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
Reads XML fragments from the OWS ServiceIdentification package v1.1.0 and
creates cows objects.

Each function expects an ElementTree node as it's first argument and returns
an cows object.

@author: Stephen Pascoe
"""

from cows.xml import ns
from cows.xml.util import *
from cows.model.service_identification import *
from cows.xml.iso19115_subset import *

def service_identification(node):
    si = ServiceIdentification(
        serviceType=code(node.find('./{%s}ServiceType' % ns.ows)),
        serviceTypeVersions=findall_text(node, './{%s}ServiceTypeVersion'
                                          % ns.ows),
        profiles=findall_text(node, './{%s}Profile' % ns.ows),
        fees=find_text(node, './{%s}Fees' % ns.ows),
        accessConstraints=find_text(node, './{%s}AccessConstraints' % ns.ows)
        )
    add_description(node, si)
    
    return si

def add_description(node, ows_object):
    """
    @note: This breaks the pattern of other functions in the cows.xml
        package.  It is needed to add attributes to subclasses of Description.
        Also it should be in a data_identification module.

    """
    ows_object.titles = findall_with(node, './{%s}Title' % ns.ows,
                                     language_string)
    ows_object.abstracts = findall_with(node, './{%s}Abstract' % ns.ows,
                                        language_string)
    ows_object.keywords = find_with(node, './{%s}Keywords' % ns.ows,
                                    keywords)
