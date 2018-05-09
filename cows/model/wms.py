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
Extends cows classes where necessary for implementing WMS 1.3.0

:author: Stephen Pascoe
"""

from cows.model.contents import DatasetSummary
from cows.model.domain import Domain

class WmsDatasetSummary(DatasetSummary):
    """
    We don't know how WMS will map Layer attributes onto an extension of DatasetSummary
    so a pragmatic approach is taken here.
    
    :ivar CRSs:
    :type CRSs: iterable of str
    :ivar styles: Style descriptors, default ['']
    :type styles: iterable of Style objects
    :ivar dimensions:
    :type dimensions: dictionary mapping dimension names to Dimension objects
    :ivar attribution:
    :type attribution: None or Attribution object
    :ivar authorityURLs:
    :type authorityURLs: iterable of AuthorityUrl objects
    :ivar dataURLs:
    :type dataURLs: dictionary mapping layer names to DataUrl objects
    :ivar featureListURLs:
    :type featureListURLS: iterable of FeatureListURL objects
    :ivar minScaleDenominator:
    :type minScaleDenominator: None or double
    :ivar maxScaleDenominator:
    :type maxScaleDenominator: None or double
    :ivar queryable:
    :type queryable: Boolean
    """
    def __init__(self, CRSs=[], styles=[''], dimensions={}, attribution=None, authorityURLs=[],
                 dataURLs=[], featureListURLs=[], metadataURLs=[], children=None,
                 minScaleDenominator=None, maxScaleDenominator=None,
                 queryable=False, **kw):
        super(WmsDatasetSummary, self).__init__(**kw)

        self.CRSs = CRSs
        self.styles = styles
        self.dimensions = dimensions
        self.attribution = attribution
        self.authorityURLs = authorityURLs
        self.dataURLs = dataURLs
        self.featureListURLs = featureListURLs
        self.minScaleDenominator = minScaleDenominator
        self.maxScaleDenominator = maxScaleDenominator
        self.queryable = queryable
        self.metadataURLs = metadataURLs
        
        if children is None: 
            self.children = []
        else:
            self.children = children

class Style(object):
    """
    :ivar name:
    :type name: str
    :ivar title:
    :type title: str
    :ivar abstract:
    :type abstract: None or str
    :ivar legendURLs:
    :type legendURLS: iterable of LegendURL objests
    :ivar styleSheetURL:
    :type styleSheetURL: None or FormattedURL object
    :ivar styleURL:
    :type styleURL: None or FormattedURL object

    """
    def __init__(self, name, title, abstract=None, legendURLs=[], styleSheetURL=None,
                 styleURL=None):
        self.name = name
        self.title = title
        self.abstract = abstract
        self.legendURLs = legendURLs
        self.styleSheetURL = styleSheetURL
        self.styleURL = styleURL

class FormattedURL(object):
    """
    :ivar format:
    :type format: str
    :ivar onlineResource:
    :type onlineResource: OnlineResource object

    """
    def __init__(self, format, onlineResource):
        self.format = format
        self.onlineResource = onlineResource

class LegendURL(FormattedURL):
    """
    :ivar width:
    :type width: None or int
    :ivar height:
    :type height: None or int

    """
    def __init__(self, width, height, **kw):
        super(LegendURL, self).__init__(**kw)
        
        self.width = width
        self.height = height

class Dimension(Domain):
    """
    Use Domain attributes where possible.
    
    :ivar multipleValues:
    :type multipleValues: boolean (default False)
    :ivar nearestValue:
    :type nearestValue: boolean (default False)
    :ivar current:
    :type current: boolean (default False)
    :ivar unitSymbol: Unit symbol could probably be taken from the Domain
        structure but it isn't clear where (the meaning or dataType
        attributes?).
    :type unitSymbol: str

    """
    def __init__(self, multipleValues=False, nearestValue=False,
                 current=False, unitSymbol=None, **kw):
        super(Dimension, self).__init__(**kw)
        
        self.multipleValues = multipleValues
        self.nearestValue = nearestValue
        self.current = current
        self.unitSymbol = unitSymbol

class DataURL(FormattedURL):
    """
    :ivar width:
    :type width: None or int
    :ivar height:
    :type height: None or int
    """
    def __init__(self, width=None, height=None, **kw):
        super(DataURL, self).__init__(**kw)
        self.width = width
        self.height = height

class MetadataURL(FormattedURL):
    """
    :ivar metadataType:
    :type metadataType: None or str
    """
    def __init__(self, metadataType=None, **kw):
        super(MetadataURL, self).__init__(**kw)
        self.type = metadataType

#
#!TODO: Other objects referenced by WmsDatasetSummary
#