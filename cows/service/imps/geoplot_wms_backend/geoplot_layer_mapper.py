# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

'''
Created on 9 Jun 2009

@author: pnorton
'''

import logging
from copy import copy

from cows.service.imps.csmlbackend.wms.csml_wms_layer_mapper import CSMLWmsLayerMapper

from cows.service.imps.geoplot_wms_backend.geoplot_layer_builder import GeoplotLayerBuilder

log = logging.getLogger(__name__)

class GeoplotLayerMapper(CSMLWmsLayerMapper):
    
    def _getBuilder(self, fileoruri):
        """
        Creates a layer builder object to be used to generate the layers
        """
        
        builder = GeoplotLayerBuilder()
        
        return builder