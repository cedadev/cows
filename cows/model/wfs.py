# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

# Copyright (C) 2008 STFC & NERC (Science and Technology Facilities Council).
# This software may be distributed under the terms of the
# Q Public License, version 1.0 or later.
# http://ndg.nerc.ac.uk/public_docs/QPublic_license.txt



from cows.model.contents import DatasetSummary

class WfsFeatureSummary(DatasetSummary):
    """ One WfsFeatureSummary corresponds to one data 'layer' e.g. Temperature PointSeries.
    """
    def __init__(self, keywords=[], outputformats=[], **kw):
        super(WfsFeatureSummary, self).__init__(**kw)
        self.outputformats=outputformats
        self.keywords = keywords
        #TODO: DefaultSRS
        
     
        
        