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
Classes modelling the OWS common package v1.1.0.

:author: Stephen Pascoe

"""

class Metadata(object):
    """
    Terminology differences between the XML schema and the UML are confusing.
    Here is a best-guess of sensible terms.
    
    :ivar content:
    :type content: Any object
    :ivar link: URL as used in the metadata XML element's href attribute
    :type link: None or str
    :ivar about: URI as used in the metadata XML element's about attribute
    :type about: None or str

    """
    def __init__(self, content=None, link=None, about=None):
        self.content = content
        self.link = link
        self.about = about

class BoundingBox(object):
    """
    :ivar lowerCorner:
    :type lowerCorner: sequence of numbers
    :ivar upperCorner:
    :type upperCorner: sequence of numbers
    :ivar crs: URI identifying the CRS unless included in a containing object
    :type crs: None or str
    :ivar dimensions: Number of dimensions
    :type dimensions: int (positive)

    """
    def __init__(self, lowerCorner, upperCorner,
                 crs=None):
        if len(lowerCorner) != len(upperCorner):
            raise ValueError, 'Corners have differing dimensionality'

        self.lowerCorner = lowerCorner
        self.upperCorner = upperCorner
        self.crs = crs
        self.dimensions = len(lowerCorner)

class WGS84BoundingBox(BoundingBox):
    """
    Constrains BoundingBox to standard lat/lon CRS (WGS84).
    """
    def __init__(self, lowerCorner, upperCorner):
        if len(lowerCorner) != 2 or len(upperCorner) != 2:
            raise ValueError, 'Corners are not of dimension 2'
        
        BoundingBox.__init__(self, lowerCorner, upperCorner,
                             crs='um:ogc:def:crs:OGC::84')
