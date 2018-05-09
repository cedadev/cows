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
Helper functions for constructing cows objects

@author: Stephen Pascoe
"""

from cows.model import *

def domain(value=None, possibleValues=None, **kwargs):
    """
    Construct a domain object.

    @param value: The defaultValue of the domain
    @param possibleValues: Either a list of possible values,
        a PossibleValues object or None to represent any value
    @param kwargs: all other arguments passed to the Domain constructor.
    """
    if possibleValues is None:
        pv = PossibleValues.fromAnyValue()
    elif isinstance(possibleValues, PossibleValues):
        pv = possibleValues
    else:
        pv = PossibleValues.fromAllowedValues(possibleValues)

    return Domain(defaultValue=value, possibleValues=pv, **kwargs)

def operation(uri, formats=[]):
    """
    Helper function for making Operation objects.

    """
    params = {'Format': domain(possibleValues=formats)}
    return Operation(get=RequestMethod(href=uri), parameters=params)

def wms_layer(name, title, srs, bbox, abstract=None):
    """
    Helper function for making wms layer descriptions.

    Parameters are mainly self explanitory.

    @param bbox: A tuple (llx, lly, urx, ury)
    
    """
    llx, lly, urx, ury = bbox

    if abstract is None:
        abstracts = []
    else:
        abstracts = [abstract]
    
    bboxObj = BoundingBox((llx, lly), (urx, ury), crs=srs)
    ds = WmsDatasetSummary(identifier=name,
                           titles=[title],
                           boundingBoxes=[bboxObj],
                           abstracts=abstracts)

    return ds

def wms_dimension(extent, units, unitSymbol):
    """
    Helper function for making wms dimension descriptions.

    @todo: More parameters like current and multipleValues need implementing.

    """
    d = Dimension(valuesUnit=units,
                  unitSymbol=unitSymbol,
                  possibleValues=PossibleValues.fromAllowedValues(extent))
    
    return d
