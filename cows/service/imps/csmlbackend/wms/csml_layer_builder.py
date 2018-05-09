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

from cows.service.imps.csmlbackend import getGlobalCSMLConnector
from cows.service.imps.csmlbackend.wms.wms_csmllayer import CSMLwmsLayer, CSMLwmsDimension
from cows.service.imps.csmlbackend.wms.csml_data_reader import CSMLDataReader

import logging

log = logging.getLogger(__name__)


class CSMLLayerBuilder(object):
  
    def __init__(self):
        self._crscat=csml.csmllibs.csmlcrs.CRSCatalogue()
        self.connector = getGlobalCSMLConnector()

    def getDSName(self, fileoruri):
        "Returns the dataset name of a given fileoruri"
        
        if self.connector.isGroup(fileoruri):
            dsName = fileoruri
        else:
            ds = self.connector.getCsmlDoc(fileoruri)
            
            try:
                dsName = ds.name.CONTENT
            except AttributeError:
                dsName = 'CSML/Geoplot WMS Service'
        
        return dsName
    
    def getTitle(self, fileoruri):
        """
        returns the layer title that corresponds to a fileoruri
        """
        dsName = os.path.split(fileoruri)[1]

        return dsName

    def getAbstract(self, fileoruri):
        
        if self.connector.isGroup(fileoruri):
            dsName = self.getTitle(fileoruri)
        
        else:
            ds = self.connector.getCsmlDoc(fileoruri)
            
            try:
                dsName = ds.name.CONTENT
            except AttributeError:
                dsName = self.getTitle(fileoruri)
        
        return dsName

    def buildRootLayers(self, fileoruri):

        log.debug("building root layer for fileoruri = %s" % (fileoruri,))

        if self.connector.isGroup(fileoruri):
            rootLayers = self._buildLayersGroup(fileoruri)
        else:
            rootLayers = self._buildDataLayers(fileoruri)
        
        return rootLayers
    
    def _buildLayersGroup(self, fileoruri):
        """
        Takes a grouping layer (one associated with a folder rather than a csml
        file) and builds layers for all the contained files + folders.
        """
        
        childLayers = []
        
        for fc in self.connector.list(folder=fileoruri):
            
            l = self._buildGroupingLayer(self.getTitle(fc), self.getAbstract(fc))
            
            # remove the default feature info formats so this layer is not
            # flagged as queryable
            l.featureInfoFormats = None
            
            # the fc is a folder
            if self.connector.isGroup(fc):
                l.childLayers = self._buildLayersGroup(fc)
            # the fc is a csml file    
            else: 
                l.childLayers = self._buildDataLayers(fc)
            
            childLayers.append(l)
        
        return childLayers

    def _buildDataLayers(self, fileoruri):
        """
        Builds a list of data layer objects that correspond to the features found
        in the csml file ascociated with the fileoruri given.
        """
        
        ds = self.connector.getCsmlDoc(fileoruri)
        
        # build a data reader to be used by all the layers
        dataReader = CSMLDataReader(fileoruri)
        
        featureList = [feature for feature in csml.csmllibs.csmlextra.listify(ds.featureCollection.featureMembers)]
        
        dataLayers = [self._buildDataLayer(feature, fileoruri, dataReader) for feature in featureList]
        
        return dataLayers

    def _buildGroupingLayer(self, title, abstract):
        """
        creates a layer object with only a title and abstract, used for containing other
        layers
        """
        return CSMLwmsLayer(title, abstract)

    def _buildDataLayer(self, feature, fileoruri, dataReader):
        """
        builds a data layer object corresponding to a csml feature
        """
        
        title, abstract, dimensions, units, crss=self._getWMSInfo(feature)
        
        bb = self._getBBox(feature)
        
        name = fileoruri.replace('/','_') + '_' +feature.id
        
        layer = CSMLwmsLayer(name=name, title=title, abstract=abstract, 
                             dimensions=dimensions, units=units, crss=crss, 
                             boundingBox=bb, dataReader=dataReader)
        
        return layer
               
    def _getFeatureTitleAndAbstract(self, feature):
        ''' given a csml feature, return basic info about the layer/feature/coverage
        @return:   title, abstract'''

        try:
            title=feature.name.CONTENT
        except:
            title=''
            
        try:
            abstract=feature.description.CONTENT
        except:
            abstract=title
        
        return title, abstract    

    def _getBBox(self, feature):
        try: 
            bb = feature.getCSMLBoundingBox().getBox()
        except:
            #default to global
            bb=[-180,-90,180,90]
        return bb        

    def _getWMSInfo(self, feature):
        ''' given a csml feature, return info about the layer/feature
        @return:   title, abstract, dimensions, units, crss '''

        title, abstract = self._getFeatureTitleAndAbstract(feature)
        units=feature.getDomainUnits()  
        dimensions={}
        tmpunits=copy(units)
        tmpunits.reverse()
        domain = feature.getDomain()
        
        for dim in feature.getAxisLabels():
            nextdim=CSMLwmsDimension(domain, dim, tmpunits.pop())
            
            if dim not in ['latitude', 'longitude']:
                dimensions[dim]=nextdim
                
        crs=feature.getNativeCRS()
        crss=[self._crscat.getCRS(crs).twoD]
        
        if 'EPSG:4326' in crss:
            crss.append('CRS:84')
            crss.append('WGS84')
                    
        #the units to return are the units of measure.
        try:
            units=feature.value.rangeSet.valueArray.valueComponent.uom
        except:
            units='unknown units'
            
        return title, abstract, dimensions, units, crss
