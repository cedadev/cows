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

import time
import os
import numpy

from cows.service.imps.csmlbackend.config import config
from cows.service.wms_iface import IwmsLayer
from ConfigParser import NoOptionError, NoSectionError

log = logging.getLogger(__name__)

import geoplot.colour_bar
import geoplot.colour_scheme

from cows.model.wms import Style, LegendURL, FormattedURL, MetadataURL
from cows.xml.iso19115_subset import OnlineResource

from pylons import url, request

from cows.service.imps.csmlbackend.wms.wms_csmllayer import CSMLwmsLayer

from cows.service.imps.geoplot_wms_backend.slabs.slab_base import SlabBase
from cows.service.imps.geoplot_wms_backend.slabs.slab_contour import SlabContour
from cows.service.imps.geoplot_wms_backend.slabs.slab_grid import SlabGrid
from cows.service.imps.geoplot_wms_backend.slabs.slab_interval import SlabInterval
from cows.service.imps.geoplot_wms_backend.slab_options_parser import SlabOptionsParser

class GeoplotWmsLayer(CSMLwmsLayer):

    slab_classes = [SlabGrid, SlabContour, SlabInterval]
    default_slab_class = SlabGrid
    
    EnableDisplayOptions = False
    EnableXMLAxisConfig = False
    EnableColourMapsConfig = True
    
    def __init__(self, title, abstract, name=None, dimensions=None, 
                       units=None, crss=None, boundingBox=None, 
                       dataReader=None, childLayers=None):
        
        CSMLwmsLayer.__init__(self, title, abstract, name=name, dimensions=dimensions,
                     units=units, crss=crss, boundingBox=boundingBox,
                     dataReader=dataReader, childLayers=childLayers)
         
        self.legendSize=(630,120)
        
        if name is not None:
            self.styles = self._buildStyles()
            self.metadataURLs = self._buildMetadataURL()
        
        self.configOptions = {}

        if GeoplotWmsLayer.EnableColourMapsConfig:       
            #dig out the name of the csml file and look up the colour map
            filename=str(request.environ['pylons.routes_dict']['fileoruri'])  
            if self.dataReader:  #sometimes it is None - for hierarchical datasets.
                cmapcfg=self.dataReader.connector.getColourMapConfig(filename)
                if cmapcfg:
                    try:
                        self.configOptions['cmap_min'] = cmapcfg.get(self.title, 'min')
                    except (NoOptionError, NoSectionError):
                        log.warning('Could not find min entry for %s in .ini file'%self.title)
                    try:
                        self.configOptions['cmap_max'] = cmapcfg.get(self.title, 'max')
                    except (NoOptionError, NoSectionError):
                        log.warning('Could not find max entry for %s in .ini file'%self.title)
                    try:
                        cmap = cmapcfg.get(self.title, 'cmap')
                        if geoplot.colour_scheme.isValidCmapName(cmap):
                            self.configOptions['cmap'] = cmap
                            log.debug('Found colour map %s for layer %s' % (cmap, self.title))

                            # Add colour map to valid values if validated.
                            for opt in SlabBase.renderingOptions:
                                if opt.name == 'cmap':
                                    optList = opt.options
                                    if cmap not in optList:
                                        optList.append(cmap)
                    except (NoOptionError, NoSectionError):
                        log.debug('Could not find colour map for layer %s' % self.title)
        
    def getSlab(self, crs, style, dimValues, transparent, bgcolor, 
                    additionalParams={}):
        """
        Creates a slab of the layer in a particular CRS and set of
        dimensions.

        @param crs: The coordinate reference system.
        @param dimValues: A mapping of dimension names to dimension values
            as specified in the IDimension.extent
        @param renderOpts: A generic mapping object for passing rendering
            options
        @return: An object implementing ILayerSlab
        #create netcdf for whole lat/lon for given dimValues, use to init slab
        """
        
        #make the colour compatable with matplotlib
        if bgcolor.find('0x') == 0:
            bgcolor = '#' + bgcolor[2:]
        
        netcdfVar = self.dataReader.getNetcdfVar(self.title, dimValues)
        
        slabClass = self._getSlabClass(style)
        
        bbox=self.getBBox(crs)
        
        # Merge in configured options for the layer.
        for k, v in self.configOptions.iteritems():
            if k not in additionalParams:
                additionalParams[k] = v

        slab = slabClass(netcdfVar, self.title, crs, dimValues, transparent, bgcolor, bbox, additionalParams)
               
        return slab

    def _getActualStyle(self, style=None):
        actualStyle = None
        
        if style == 'default' or style == '' or style is None:
            actualStyle = GeoplotWmsLayer.default_slab_class.style
        else:
            actualStyle = style
        
        if actualStyle not in [x.style for x in GeoplotWmsLayer.slab_classes]:
            Exception("No slab class found for style = %s"  % (style,))
             
        return actualStyle
    
    def _getSlabClass(self, style):
        slabClass = None
        
        s = self._getActualStyle(style)
        
        for klass in GeoplotWmsLayer.slab_classes:
            if klass.style == s:
                slabClass = klass
                break
        
        if slabClass == None:
            Exception("No slab class found for style = %s"  % (style,))
        
        return slabClass

    def getFeatureInfo(self, format, crs, point, dimValues):
        """
        Return a response string descibing the feature at a given
        point in a given CRS.

        Currently only "html" is supported as output format

        @param format: One of self.featureInfoFormats.  Defines which
            format the response will be in.
        @param crs: One of self.crss
        @param point: a tuple (x, y) in the supplied crs of the point
            being selected.
        @param dimValues: A mapping of dimension names to dimension values.
        @return: A string containing the response.

        """
        netcdf = self.dataReader.getNetcdfVar(self.title, dimValues)
       
        #Now grab the netCDF object for the point specified.
        #The reason for the 'cob' option is so that if the grid the data 
        #is defined on does not have a grid point at the point specified, 
        #we should  still get the nearest location
        
        try:
            t_point = netcdf(latitude=(point[1], point[1], 'cob'), longitude=(point[0], point[0], 'cob'))
        except Exception, exc:
            value = "Value not available for the requested position"
            log.debug(value + ": " + str(point[1]) + ", " + str(point[0]) + ": " + exc.__str__())
            return value

        #now get the value recorded at this location
        value = t_point.getValue().tolist()
        log.debug(value)
        log.debug(t_point.fill_value)
        #and the fill_value too
        fill_value = t_point.fill_value
        #value is actually embedded in a multi dimensional list, 
        #so we need to extract the actual value from the list
        while type(value) is list:
                value = value[0]

        #now check if the value is actually the fill_value rather than 
        #a value recorded at the point specified
        log.debug('%s %s' % (value, fill_value))
        if (2*fill_value) == value:
            log.debug("No value found at position: "+str(point[1])+", "+str(point[0]))
        else:
            value = str(value)

        # finally return the value
        log.debug('Response "%s"' % value)
        return value

    def getLegendImage(self, dimValues, width=None, height=None, 
                       orientation='horizontal', 
                       renderOpts={}, 
                       style=None
                       ):
        """
        Create an image of the colourbar for this layer.
        @param orientation: Either 'vertical' or 'horizontal'
        @return: A PIL image with labels 

        """
        if width == None:
            width = self.legendSize[0]
            
        if height == None:
            height = self.legendSize[1]
        variable = self.dataReader.getNetcdfVar(self.title, dimValues)
        klass = self._getSlabClass(style)

        # Merge in configured options for the layer.
        for k, v in self.configOptions.iteritems():
            if k not in renderOpts:
                renderOpts[k] = v
                log.debug("Using layer default for %s: %s" % (k, v))

        parser=SlabOptionsParser(klass.renderingOptions, renderOpts)
        log.debug("parser.getOption('cmap') %s" % parser.getOption('cmap'))
        
        return klass.makeColourBar(width , height, orientation, self.units, renderOpts, variable)
    
        #none of the below code is run anymore?
#        parser = SlabOptionsParser(klass.renderingOptions, renderOpts)
#        
#        log.debug("klass.style = %s" % (klass.style,))
#        minval = parser.getOption('cmap_min') #user supplied takes priority
#        if minval == None:
#            minval = variable.min()
#            
#        maxval = parser.getOption('cmap_max')
#        if maxval == None:
#            maxval = variable.max()
#            
#            # can't have a colourbar with an infinite maximum, take the highest 
#            # non-inf value.
#            if maxval == numpy.inf:
#                maxval = numpy.ma.masked_equal(variable, numpy.inf).max()
#        
#        log.debug("parser.getOption('intervals') = %s" % (parser.getOption('intervals'),))
#        log.debug("parser.getOption('intervalNames') = %s" % (parser.getOption('intervalNames'),))
#        
#        im = geoplot.colour_bar.getColourBarImage(width, height, 
#                                             label='Units of measure: %s' % str(self.units),
#                                             cmap=parser.getOption('cmap'), 
#                                             colourBarMin=minval,
#                                             colourBarMax=maxval,
#                                             colourBarScale=parser.getOption('cmap_scale'),
#                                             numIntervals=parser.getOption('num_intervals'), 
#                                             orientation=orientation,
#                                             intervals=parser.getOption('intervals'),
#                                             intervalNames=parser.getOption('intervalNames'),
#                                             colourBarStyle=parser.getOption('cbar_style'),
#                                             )
#        
#        return im
    
    def _buildStyles(self):
        onlineRes = OnlineResource(self._getIndexActionURL() + "?request=GetLegend&layers=%s" % self.name)
        
        legendURL = LegendURL(630, 80, format='img/png', onlineResource=onlineRes )
        
        styles = []
        for klass in GeoplotWmsLayer.slab_classes:
            
            styleName = klass.style
            
            title = getattr(klass, 'title', None)
            
            if title is None:
                title = styleName
            
            s = Style(styleName, title, legendURLs=[legendURL] )
            
            styles.append(s)
        
        return styles
    
    def getAxisConfigFile(self):
        xmlFile = None
        
        if hasattr(self.dataReader, 'getConfigAxisXMLFile'):
            
            xmlFile =  self.dataReader.getConfigAxisXMLFile()
        
        return xmlFile
    
    def _buildMetadataURL(self):
        
        metadataURLs = []
        
        if GeoplotWmsLayer.EnableDisplayOptions == True:
            onlineRes = OnlineResource(self._getIndexActionURL() +\
                       "?request=GetDisplayOptions&layers=%s" % self.name)
            
            metadataURLs.append( MetadataURL(metadataType='display_options', 
                                          format='application/json',
                                          onlineResource=onlineRes) )
            
        if GeoplotWmsLayer.EnableXMLAxisConfig:
            
            xmlFile =  self.getAxisConfigFile()
            
            if xmlFile != None:
                
                onlineRes = OnlineResource(self._getIndexActionURL() +\
                                "?request=GetAxisConfig&layers=%s" % self.name)
            
                metadataURLs.append( MetadataURL(metadataType='axis_config', 
                                                 format='text/xml',
                                                 onlineResource=onlineRes) )      
        
        return metadataURLs
    
    def _getIndexActionURL(self):
        """
        Uses the pylons config to build a url for the index action of this contoller.
        """
                
        indexURL = url.current(qualified=True, action='index')
        return indexURL
