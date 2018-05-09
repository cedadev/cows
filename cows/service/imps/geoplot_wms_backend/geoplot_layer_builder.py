# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

'''
Created on 22 Jan 2010

@author: pnorton
'''


from copy import copy
import csml
import os


from cows.service.imps.csmlbackend.wms.csml_layer_builder import CSMLLayerBuilder

from cows.service.imps.geoplot_wms_backend.geoplot_wms_layer import GeoplotWmsLayer

import logging

log = logging.getLogger(__name__)


class GeoplotLayerBuilder(CSMLLayerBuilder):
  

    def _buildGroupingLayer(self, title, abstract):
        return GeoplotWmsLayer(title, abstract)

    def _buildDataLayer(self, feature, fileoruri, dataReader):
        """
        builds a data layer object corresponding to a csml feature
        """
        
        title, abstract, dimensions, units, crss=self._getWMSInfo(feature)
        
        bb = self._getBBox(feature)
        
        name = fileoruri.replace('/','_') + '_' +feature.id
        
        layer = GeoplotWmsLayer(name=name, title=title, abstract=abstract, 
                                 dimensions=dimensions, units=units, crss=crss, 
                                 boundingBox=bb, dataReader=dataReader)
        
        return layer
