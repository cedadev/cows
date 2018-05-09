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
Classes modelling the OWS Contents package v1.1.0.

:author: Stephen Pascoe
"""

from cows.model.iso19115_subset import Keywords
from cows.model.data_identification import Description

class Contents(object):
    """
    :ivar datasetSummaries:
    :type datasetSummaries: Iterable of DatasetSummary objects
    :ivar otherSources: URLs
    :type otherSource: iterable of str

    """
    def __init__(self, datasetSummaries=None, otherSources=None):
        if datasetSummaries is None:
            self.datasetSummaries = []
        else:
            self.datasetSummaries = datasetSummaries
        if otherSources is None:
            self.otherSources = []
        else:
            self.otherSources = otherSources

class DatasetSummary(Description):
    """
    :ivar identifier:
    :type identifier: None, str or Code
    :ivar datasetSummaries:
    :type datasetSummaries: Iterable of DatasetSummary objects
    :ivar metadata:
    :type metadata: iterable of Metadata objects
    :ivar boundingBoxes:
    :type boundingBoxes: iterable of BoundingBox objects
    :ivar wgs84BoundingBoxes:
    :type wgs84BoundingBoxes: iterable of WSG84BoundingBox objects
    """

    def __init__(self, titles=[], abstracts=[], keywords=Keywords(),
                 identifier=None, datasetSummaries=[], metadata=[], boundingBoxes=[],
                 wgs84BoundingBoxes=[]):
        super(DatasetSummary, self).__init__(titles, abstracts, keywords)

        self.identifier = identifier
        self.datasetSummaries = datasetSummaries
        self.metadata = metadata
        self.boundingBoxes = boundingBoxes
        self.wgs84BoundingBoxes = wgs84BoundingBoxes
