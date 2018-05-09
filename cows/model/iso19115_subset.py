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
Classes modelling the OWS ISO19115 subset package v1.1.0.

:author: Stephen Pascoe
"""

class LanguageString(str):
    """
    If you wish to attach a language identifier to a string use this
    class.  Otherwise normal strings can be used in place of LanguageString.
    
    :ivar lang: language identifier
    :type lang: str

    """

    def __new__(cls, value='', lang=None):
        return str.__new__(cls, value)
    
    def __init__(self, value='', lang=None):
        self.lang = lang

class Code(str):
    """
    If you wish to attach a codeSpace to a Code element use this class,
    otherwise it can be substituted with a string

    :ivar code:
    :type code: str
    :ivar codeSpace: URI qualifying self.code
    :type codeSpace: None or char

    """

    def __new__(cls, code='', codeSpace=None):
        return str.__new__(cls, code)

    def __init__(self, code='', codeSpace=None):
        self.codeSpace = codeSpace

class Keywords(list):
    """
    If you wish to attach a type code to a keyword list use this class.
    Otherwise any iterable can be used in place of Keywords.

    :ivar type:
    :type type: Code

    """
    __slots__ = ['type']

    def __new__(cls, value=[], type=None):
        return list.__new__(cls, value)

    def __init__(self, value=[], type=None):
        self.type = type
        
class Xlink(object):
    """
    This class exposes all xlink:simpleLink attributes.

    :ivar href: A URL
    :type href: str
    :ivar role:
    :type role: None or str
    :ivar show:
    :type show: None or str
    :ivar title:
    :type title: None or str
    :ivar actuate:
    :type actuate: None or str
    :ivar arcrole:
    :type arcrole: None or str

    """
    def __init__(self, href, role=None, show=None, title=None, actuate=None,
                 arcrole=None):
        self.href = href
        self.role = role
        self.show = show
        self.title = title
        self.actuate = actuate
        self.arcrole = arcrole

class OnlineResource(Xlink):
    pass


#ResponsibleParty, Address, Telephone, & Contact classes added by D.Lowe
class ResponsibleParty(object):
    """
    :ivar individualName:
    :type individualName: None or str
    :ivar positionName:
    :type positionName: None or str
    :ivar role:
    :type role: None or Code
    :ivar contactInfo:
    :type contactInfo: None or Contact
    """
    def __init__(self, individualName=None, positionName=None, role=None, contactInfo=None):
        self.individualName=individualName
        self.positionName=positionName
        self.role=role    
        self.contactInfo=contactInfo

class Address(object):
    """
    :ivar deliveryPoints:
    :type deliveryPoints: iterable of str objects
    :ivar city:
    :type city: None or str
    :ivar administrativeArea:
    :type administrativeArea: None or str
    :ivar postalCode:
    :type postalCode: None or str
    :ivar country:
    :type country: None or str
    :ivar electronicMailAddress:
    :type electronicMailAddress: None or str
   
    """
    def __init__(self, deliveryPoints=[],city=None, administrativeArea=None, postalCode=None, country=None, electronicMailAddress=None):
        self.deliveryPoints=deliveryPoints
        self.city=city
        self.administrativeArea=administrativeArea
        self.postalCode=postalCode
        self.country=country
        self.electronicMailAddress=electronicMailAddress       

class Telephone(object):
   """
   :ivar voice:
   :type voice: None or str
   :ivar facsimile:
   :type facsimile: None or str
   """
   def __init__(self, voice=None, facsimile=None):
       self.voice=voice
       self.facsimile=facsimile

class Contact(object):
    """
    :ivar hoursOfService:
    :type hoursOfService: None or str
    :ivar contactInstructions:
    :type contactInstructions: None or str
    :ivar address:
    :type address: None or Address
    :ivar phone:
    :type phone: None or Telephone
    :ivar onlineResource:
    :type onlineResource: None or OnlineResource
    """
    def __init__(self, hoursOfService=None, contactInstructions=None, address=None, phone=None, onlineResource=None):
        self.hoursOfService=hoursOfService
        self.contactInstructions=contactInstructions
        self.address=address
        self.phone=phone
        self.onlineResource=onlineResource
