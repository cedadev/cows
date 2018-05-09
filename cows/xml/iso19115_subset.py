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
Reads XML fragments from the OWS ISO19115 subset package v1.1.0 and
creates cows objects.

Each function expects an ElementTree node as it's first argument and returns
an cows object.

@author: Stephen Pascoe
"""

from cows.xml import ns
from cows.xml.util import *
from cows.model.iso19115_subset import *


def language_string(node):
    try:
        lang = node.attrib['{%s}lang' % ns.xml]
    except KeyError:
        return node.text

    return LanguageString(node.text, lang)

def keywords(node):
    type_n = node.find('./{%s}Type' % ns.ows)
    if type_n is None:
        kl = []
    else:
        kl = Keywords([], code(type_n))

    for k_n in node.findall('./{%s}Keyword' % ns.ows):
        kl.append(language_string(k_n))

    return kl

def code(node):
    try:
        codeSpace = node.attrib['{%s}codeSpace' % ns.ows]
    except KeyError:
        return node.text

    return Code(node.text, codeSpace)
    
def xlink(node):
    xl = Xlink(node.attrib['{%s}href'%ns.xlink])

    for a in ['role', 'show', 'title', 'actuate', 'arcrole']:
        setattr(xl, a, node.attrib.get('{%s}%s' % (ns.xlink, a)))

    return xl

def online_resource(node):
    return xlink(node)

def responsible_party(node):
    rp = ResponsibleParty(
        individualName=find_text(node, './{%s}IndividualName' % ns.ows),
        positionName=find_text(node, './{%s}PositionName' % ns.ows),
        role=find_with(node, './{%s}Role' % ns.ows, code),
        contactInfo=find_with(node, './{%s}ContactInfo' % ns.ows, contact)
        )
    return rp

def contact(node):
    ci = Contact(
        hoursOfService=find_text(node, './{%s}HoursOfService' % ns.ows),
        contactInstructions=find_text(node, './{%s}ContactInstructions'
                                       % ns.ows),
        address=find_with(node, './{%s}Address' % ns.ows, address),
        phone=find_with(node, './{%s}Phone' % ns.ows, telephone),
        onlineResource=find_with(node, './{%s}OnlineResource' % ns.ows,
                                  online_resource)
        )
    return ci

def address(node):
    a = Address(
        deliveryPoints=findall_text(node, './{%s}DeliveryPoint' % ns.ows),
        city=find_text(node, './{%s}City' % ns.ows),
        administrativeArea=find_text(node, './{%s}AdministrativeArea'
                                      % ns.ows),
        postalCode=find_text(node, './{%s}PostalCode' % ns.ows),
        country=find_text(node, './{%s}Country' % ns.ows),
        electronicMailAddress=find_text(node, './{%s}ElectronicMailAddress'
                                         % ns.ows)
        )
    return a

def telephone(node):
    t = Telephone(
        voice=find_text(node, './{%s}Voice' % ns.ows),
        facsimile=find_text(node, './{%s}Facsimile' % ns.ows)
        )
    return t
