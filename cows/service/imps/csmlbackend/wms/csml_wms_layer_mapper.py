# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

'''
Created on 25 Jan 2010

@author: pnorton
'''
'''
Created on 9 Jun 2009

@author: pnorton
'''

import logging
from copy import copy

from cows.service.wxs_iface import ILayerMapper

from cows.service.imps.csmlbackend.wms.csml_layer_builder import CSMLLayerBuilder

log = logging.getLogger(__name__)

class CSMLWmsLayerMapper(ILayerMapper):
    
    def __init__(self):
        self.layermapcache={}
   
    def map(self, **kwargs):
        """
        Given csml.parser.Dataset object list the names of
        all layers available.
        
        @return: A mapping of layer names to ILayer implementations.
        @raise ValueError: If no layers are available for these keywords. 
        """
        fileoruri=kwargs['fileoruri']
        
        if fileoruri in self.layermapcache.keys():
            
            log.debug("cached layermap used for fileoruri = %s" % (fileoruri,))
            
            self.datasetName = self.layermapcache[fileoruri]['dsName'] 
            #we've accessed this layer map before, get it from the cache dictionary
            return self.layermapcache[fileoruri]['layermap']
        

        log.debug("loading layermap for fileoruri = %s" % (fileoruri,))
        layermap={}
        
        builder = self._getBuilder(fileoruri)
        
        self.datasetName = builder.getDSName(fileoruri)
        
        for layer in builder.buildRootLayers(fileoruri):
            layermap[layer.title] = layer
        
        if len(layermap) > 0:
            self.layermapcache[fileoruri]={'layermap':layermap, 'dsName':self.datasetName}
            return layermap
        else:
            raise ValueError
        
    def _getBuilder(self, fileoruri):
        """
        Creates a layer builder object to be used to generate the layers
        """
        
        builder = CSMLLayerBuilder()
        
        return builder