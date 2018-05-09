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
Classes modelling the OWS Data Identification package v1.1.0.

:author: Stephen Pascoe
"""

from cows.model.iso19115_subset import Keywords

class Description(object):
    """
    :ivar titles:
    :type titles: iterable of str or LanguageString
    :ivar abstracts:
    :type abstracts: iterable of str or LanguageString
    :ivar keywords:
    :type keywords: iterable or Keywords

    """
    def __init__(self, titles=[], abstracts=[], keywords=Keywords()):
        self.titles = titles
        self.abstracts = abstracts
        self.keywords = keywords

class BasicIdentification(Description):
    """
    :ivar identifier:
    :type identifier: None or Code
    :ivar metadata:
    :type metadata: iterable of Metadata

    """
    def __init__(self,  identifier=None, metadata=[], **kwargs):
        super(BasicIdentification, self).__init__(**kwargs)

        self.identifier = identifier
        self.metadata = metadata

    
class Identification(BasicIdentification):
    """
    :ivar outputFormats:
    :type outputFormats: iterable of str
    :ivar availableCRSs: URIs of available coordinate reference systems
    :type availableCRSs: iterable of str

    :ivar boundingBoxes:
    :type boundingBoxes: iterable of BoundingBox

    """
    def __init__(self, outputFormats=[],
                 availableCRSs=[], boundingBoxes=[], **kwargs):
        super(Identification, self).__init__(**kwargs)

        self.outputFormats = outputFormats
        self.availableCRSs = availableCRSs
        self.boundingBoxes = boundingBoxes
        
