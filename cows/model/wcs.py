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

@author: Dominic Lowe, Stephen Pascoe
"""

#NOTE, much of this is straight from WMS and needs to be overhauled. TODO


from cows.model.contents import Contents, DatasetSummary
from cows.model.domain import Domain

import logging
log = logging.getLogger(__name__)

class WcsDatasetSummary(DatasetSummary):
    """
    """
    def __init__(self, CRSs=[], description=None, formats=[],supportedCRSs=[],timepositions=[],timelimits=[],axisdescriptions=[], **kw):
        super(WcsDatasetSummary, self).__init__(**kw)
        self.CRSs = CRSs
        self.description=description
        self.formats=formats
        self.supportedCRSs=supportedCRSs
        self.timePositions=timepositions
        self.timeLimits=timelimits
        self.axisDescriptions=axisdescriptions


class CoverageDescription(WcsDatasetSummary): 
    """
    Further extends WCSDatasetSummary to provide a fuller coverage description
    used in DescribeCoverageResponse. Building up this extra information may require more 
    work on the servers part, hence this is currently a separate class from the simpler WcsDatasetSummary.
    TODO: perhaps this isn't necessary..
    """
    def __init__(self, **kw):
        super(CoverageDescription, self).__init__(**kw)
#       TODO, add DescribeCoverage extensions
