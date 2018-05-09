# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
WMS controller for OGC Web Services (OWS).

@author: Stephen Pascoe
"""

import re
import math
from cStringIO import StringIO
from sets import Set
from pylons import request, response, config, url
from pylons import tmpl_context as c
from routes.util import GenerationException
from string import upper
import logging
log = logging.getLogger(__name__)

try: 
    from PIL import Image
except ImportError:
    import Image

from genshi.template import NewTextTemplate

from cows.model.wms import WmsDatasetSummary, Dimension, DataURL
from cows.model import PossibleValues, WGS84BoundingBox, BoundingBox, Contents
from cows.pylons import ows_controller
from cows.exceptions import *
from cows import bbox_util

class WMSController(ows_controller.OWSController):
    """
    Subclass this controller in a pylons application and set the layerMapper
    class attribute to implement a WMS.

    @cvar layerMapper: an cows.service.wms_iface.ILayerMapper object.

    """
    layerMapper = None
    #layers = {}    
    _pilImageFormats = {
        'image/png': 'PNG',
        'image/jpg': 'JPEG',
        'image/gif': 'GIF',
        'image/tiff': 'TIFF'
        }
    _layerSlabCache = {}

    #-------------------------------------------------------------------------
    # Attributes required by OWSController

    service = 'WMS'
    owsOperations = (ows_controller.OWSController.owsOperations +
        ['GetMap', 'GetContext', 'GetLegend', 'GetFeatureInfo', 'GetInfo'])
    
    validVersions = ['1.1.1', '1.3.0']

    #-------------------------------------------------------------------------

    def __before__(self, **kwargs):
        """
        This default implementation of __before__() will pass all routes
        arguments to the layer mapper to retrieve a list of layers for
        this WMS.

        It will be called automatically by pylons before each action method.

        @todo: The layer mapper needs to come from somewhere.

        """
        #self.updateSequence = "hello"
        log.debug("loading layers")
        #print self.layers
        self.layers = self.layerMapper.map(**kwargs)

    #-------------------------------------------------------------------------
    # Methods implementing stubs in OWSController

    def _renderCapabilities(self, version, format):
        if format == 'application/json':
            t = ows_controller.templateLoader.load('wms_capabilities_json.txt',
                                                   cls=NewTextTemplate)
        elif version == '1.1.1':
            t = ows_controller.templateLoader.load('wms_capabilities_1_1_1.xml')
        elif version == '1.3.0':
            t = ows_controller.templateLoader.load('wms_capabilities_1_3_0.xml')
        else:
            # We should never get here!  The framework should raise an exception before now.
            raise RuntimeError("Version %s not supported" % version)
        
        return t.generate(c=c).render()

    def _loadCapabilities(self):
        """
        @note: Assumes self.layers has already been created by __before__().

        """
        #!TODO: Add json format to GetCapabilities operation

        ows_controller.addOperation('GetMap', formats=self._pilImageFormats.keys())
        ows_controller.addOperation('GetContext', formats=['text/xml', 'application/json'])
        ows_controller.addOperation('GetLegend',
                                    formats=['image/png'])
        ows_controller.addOperation('GetInfo')
        
        featureInfoFormats = Set()

        log.debug('Loading capabilities contents')
        c.capabilities.contents = Contents()
                
        for layerName, layer in self.layers.items():

            ds = self._buildWMSDatasetSummary(layer, featureInfoFormats)
            
            c.capabilities.contents.datasetSummaries.append(ds)
        
        
        log.debug('Setting dataset name')
        
        #LayerMapper may optionally implement a datasetName attribute which 
        #will be tried if serviceIdentification/title is not supplied in capabilities config
        if c.capabilities.serviceIdentification.titles[0] is None:
                try:
                    c.capabilities.serviceIdentification.titles=[self.layerMapper.datasetName]
                except AttributeError:
                    pass
        
        # if there is still no serviceIdentification, use the fileoruri
        if c.capabilities.serviceIdentification.titles[0] is None:
            fileoruri = request.environ['pylons.routes_dict']['fileoruri']
            c.capabilities.serviceIdentification.titles=[fileoruri]
                
        # Add this operation here after we have found all formats
        ows_controller.addOperation('GetFeatureInfo',
                                    formats = list(featureInfoFormats))


    def _buildWMSDatasetSummary(self, layer, featureInfoFormats):
        
        if hasattr(layer, 'wgs84BBox'):
            wgs84BBox = WGS84BoundingBox(layer.wgs84BBox[:2],
                                         layer.wgs84BBox[2:])
        else:
            wgs84BBox = None
            
        # Get CRS/BBOX pairs
        bboxObjs = []
        
        if hasattr(layer, 'crss') and layer.crss is not None:
            for crs in layer.crss:
                bbox = layer.getBBox(crs)
                bboxObjs.append(BoundingBox(bbox[:2], bbox[2:], crs=crs))
                
        # Get dimensions
        dims = {}
        
        if hasattr(layer, 'dimensions') and layer.dimensions is not None:
            for dimName, dim in layer.dimensions.items():
                dimParam = self._mapDimToParam(dimName)
                dims[dimParam] = Dimension(valuesUnit=dim.units, unitSymbol=dim.units,
                                          possibleValues=
                                            PossibleValues.fromAllowedValues(dim.extent))
            
            
        # Does the layer implement GetFeatureInfo?
        if layer.featureInfoFormats:
            queryable = True
            featureInfoFormats.union_update(layer.featureInfoFormats)
        else:
            queryable = False
            
        if layer.name != None:
            #URL to WCS - uses named route 'wcsroute'
            #TODO: Allow for a WCS blacklist to opt out of providing dataurls for certain datasets?
            #TODO: How to make this more configurable - what if WCS is not coupled with WMS?
            try:
                version='1.0.0' #wcs version
                wcsbaseurl=url('wcsroute', fileoruri=c.fileoruri,qualified=True)+'?'
                dataURLs=[DataURL(format='WCS:CoverageDescription', onlineResource='%sService=WCS&Request=DescribeCoverage&Coverage=%s&Version=%s'%(wcsbaseurl, layer.name, version))]
            except GenerationException:
                log.info("dataURLs not populated: could not generate WCS url with url('wcsroute', filedoruri=%s,qualified=True)"%c.fileoruri)
                dataURLs=[]
        else:
            dataURLs = []
        
        
        if hasattr(layer, 'styles'):
            styles = layer.styles
        else:
            styles = ['']
        
        if hasattr(layer, 'metadataURLs'):
            metadataURLs = layer.metadataURLs
        else:
            metadataURLs = []
        
        children = []
        
        if hasattr(layer, 'childLayers'):
            children = [self._buildWMSDatasetSummary(l, featureInfoFormats) \
                                                     for l in layer.childLayers]
        
        # Create the cows object
        ds = WmsDatasetSummary(identifier=layer.name,
                               titles=[layer.title],
                               CRSs=layer.crss,
                               wgs84BoundingBoxes=[wgs84BBox],
                               boundingBoxes=bboxObjs,
                               abstracts=[layer.abstract],
                               dimensions=dims,
                               queryable=queryable,
                               dataURLs=dataURLs,
                               styles=styles,
                               children=children,
                               metadataURLs=metadataURLs)

        # Stuff that should go in the capabilities tree eventually
        ds.legendSize = layer.legendSize
        ds.legendFormats = ['image/png']        

        return ds

    def _getLayerParamInfo(self, paramName='layers'):
        """
        Retrieve the layers parameter enforcing the rule of only
        selecting one layer.

        @param paramName: Overrides the query string parameter name to
            look for.  This is usefull for implementing GetFeatureInfo.

        """
        layerName = self.getOwsParam(paramName)

        # Select the first layer if several are requested.
        # This plays nicer with mapClient.
        if ',' in layerName:
            raise InvalidParameterValue(
                'Multi-layer GetLegend requests are not supported', 'layers')
            
        layerObj = self._getLayerFromMap(layerName)
        
        return layerName, layerObj
    
    def _getLayerParam(self, paramName='layers'):
        """
        Retrieve the layers parameters.

        @param paramName: Overrides the query string parameter name to
            look for.  This is useful for implementing GetFeatureInfo.

        """
        layerNames = self.getOwsParam(paramName)
        
        layerNames = layerNames.split(',')
        
        layerObjects = [ self._getLayerFromMap(name) for name in layerNames]
        
        return layerObjects
    
    def _getLayerFromMap(self, layerName):
        """
        Searches the layer map for the named layer, if no matching layer
        is found an InvalidParameterValue is raised.
        """
        
        layerObj = None
        
        if layerName in self.layers:
            layerObj = self.layers[layerName]
        else:
            
            fileoruri = request.environ['pylons.routes_dict']['fileoruri']
            log.debug("fileoruri = %s" % (fileoruri,))
            if layerName.find(fileoruri + "_") == 0:
                
                reducedName = layerName[len(fileoruri + "_") :]
                layerObj = self._searchLayerChildren(self.layers.values(), reducedName)
        
        if layerObj is None:
            raise InvalidParameterValue('Layer %s not found, layerNames = %s' 
                                        % (layerName, self.layers.keys()))
        
        return layerObj
    
    def _searchLayerChildren(self, layerList, name):
        layerObj = None
               
        for l in layerList:
            # does this layer match?
            if l.title == name:
                layerObj = l
                break
            
            # does this layer have a child that matches?
            if name.find(l.title + "_") == 0:
                
                reducedName = name[len(l.title + "_"):]
                
                found = self._searchLayerChildren(l.childLayers, reducedName)
                
                if found is not None:
                    layerObj = found
                    break

        return layerObj


    def _getFormatParam(self):
        format = self.getOwsParam('format', default='image/png')
        if format not in self._pilImageFormats:
            raise InvalidParameterValue(
                'Format %s not supported' % format, 'format')

        return format

    _escapedDimNames = ['width', 'height', 'version', 'request',
                        'layers', 'styles', 'crs', 'srs', 'bbox',
                        'format', 'transparent', 'bgcolor',
                        'exceptions']

    def _getDimValues(self, layerObj):
        dimValues = {}
        for dimName, dim in layerObj.dimensions.items():
            defaultValue = dim.extent[0]
            escapedDimName=self._mapDimToParam(dimName)
            dimValues[escapedDimName] = self.getOwsParam(escapedDimName,
                                                  default=defaultValue)
        return dimValues

    def _mapDimToParam(self, dimName):
        """
        Dimension names might clash with WMS parameter names, making
        them inaccessible in WMS requests.  This method maps a
        dimension name to a parameter name that appears in the
        capabilities document and WMS requests.

        """
        if dimName.lower() in self._escapedDimNames:
            return dimName+'_dim'
        else:
            return dimName
        
    def _mapParamToDim(self, dimParam):
        """
        Maps a dimension parameter name to it's real dimension name.

        @see: _mapDimToParam()

        """
        try:
            dimName = re.match(r'(.*)_dim$', dimParam).group(1)
            if dimName.lower() in self._escapedDimNames:
                return dimName
            else:
                return dimParam
        except AttributeError:
            return dimParam


    def _retrieveSlab(self, layerObj, srs, style, dimValues, transparent, bgcolor, additionalParams):
        
        # Find the slab in the cache first
        cacheKey = layerObj.getCacheKey(srs, style, dimValues, transparent, bgcolor, additionalParams)
        slab = self._layerSlabCache.get(cacheKey)
        
        if slab is None:
            
            slab = layerObj.getSlab(srs, style, dimValues, transparent, bgcolor, additionalParams)
            
            if cacheKey is not None:
                self._layerSlabCache[cacheKey] = slab

        return slab

    #-------------------------------------------------------------------------
    # OWS Operation methods
    
    def GetMap(self):

        # Get the parameters
        version      = self._getVersionParam()
        format       = self._getFormatParam()        
        transparent  = self._getTransparentParam()
        bgcolor      = self._getBgcolorParam()
        bbox         = self._getBboxParam()
        width        = self._getWidthParam()
        height       = self._getHeightParam()
        
        layerObjects = self._getLayerParam()
        
        styles       = self._getStylesParam(len(layerObjects))
        srs          = self._getSrsParam(version)
        
        log.debug("layerNames = %s" % ([o.name for o in layerObjects],))
        
        finalImg = Image.new('RGBA', (width, height), (0,0,0,0))

        # Multiple Layers handling..  
        for i in range(len(layerObjects)):
            layerObj = layerObjects[i]
            
                        
            #if no styles  provided, set style = ""            
            if styles =="":
                style = ""
            else:
                style = styles[i]
                            
            #if style parameter is "default", set style = ""
            if upper(style) == 'DEFAULT':
                style=""
            
            if srs not in layerObj.crss:
                raise InvalidParameterValue('Layer %s does not support SRS %s' % (layerObj.name, srs))

            dimValues = self._getDimValues(layerObj)
            
            #now need to revert modified dim values (e.g. height_dim) back to dim values the layerMapper understands (e.g. height)
            restoredDimValues={}
            for dim in dimValues:
                restoredDim=self._mapParamToDim(dim)
                restoredDimValues[restoredDim]=dimValues[dim]
            
            expectedParams = []
            expectedParams.extend(self._escapedDimNames)
            expectedParams.extend(layerObj.dimensions.keys())
            
            #get any other parameters on the request that the layer might need
            additionalParams = self._getAdditionalParameters(expectedParams)
            
            slab = self._retrieveSlab(layerObj, srs, style, restoredDimValues, 
                                      transparent, bgcolor, additionalParams)

            bbox = self._convertBboxForCrs(bbox, version, srs)

            img = slab.getImage(bbox, width, height)
            
            finalImg = Image.composite(finalImg, img, finalImg)    

        # IE 6.0 doesn't display the alpha layer right.  Here we sniff the
        # user agent and remove the alpha layer if necessary.
        try:
            ua = request.headers['User-Agent']
            log.debug("ua = %s" % (ua,))
        except:
            pass
        else:
            if 'MSIE 6.0' in ua:
                finalImg = finalImg.convert('RGB')

        self._writeImageResponse(finalImg, format)


    def GetContext(self):
        """
        Return a WebMap Context document for a given set of layers.

        """
        # Parameters
        layers = self.getOwsParam('layers', default=None)
        format = self.getOwsParam('format', default='text/xml')

        # Filter self.layers for selected layers
        if layers is not None:
            newLayerMap = {}
            for layerName in layers.split(','):
                try:
                    newLayerMap[layerName] = self.layers[layerName]
                except KeyError:
                    raise InvalidParameterValue('Layer %s not found' % layerName,
                                                'layers')
                    
            self.layers = newLayerMap

        # Automatically select the first bbox/crs for the first layer
        aLayer = self.layers.values()[0]
        crs = aLayer.crss[0]
        bb = aLayer.getBBox(crs)
        c.bbox = BoundingBox(bb[:2], bb[2:], crs)

        # Initialise as if doing GetCapabilities
        ows_controller.initCapabilities()
        self._loadCapabilities()

        if format == 'text/xml':
            response.headers['Content-Type'] = format
            t = ows_controller.templateLoader.load('wms_context_1_1_1.xml')
            return t.generate(c=c).render()
        elif format == 'application/json':
            response.headers['Content-Type'] = format
            t = ows_controller.templateLoader.load('wms_context_json.txt',
                                                   cls=NewTextTemplate)
            return t.generate(c=c).render()
        else:
            raise InvalidParameterValue('Format %s not supported' % format)

    def GetFeatureInfo(self):
        # Housekeeping
        version = self.getOwsParam('version', default=self.validVersions[0])
        if version not in self.validVersions:
            raise InvalidParameterValue('Version %s not supported' % version,
                                        'version')

        # Coordinate parameters
        bbox = tuple(float(x) for x in self.getOwsParam('bbox').split(','))
        width = int(self.getOwsParam('width'))
        height = int(self.getOwsParam('height'))
          
        # Get pixel location
        i = int(self.getOwsParam('i'))
        j = int(self.getOwsParam('j'))
        
        format = self.getOwsParam('info_format', default='text/html')

        layers = self._getLayerParam('query_layers')
        for layerObj in layers:
            layerName = layerObj.name
            log.debug('Format: %s' % format)
            log.debug('Title: %s' % layerObj.title)
            log.debug('FeatureInfoFormats: %s' % layerObj.featureInfoFormats)
        
        # ### Only process first layer if more than one. ###
        layerObj = layers[0]
        
        if format not in layerObj.featureInfoFormats:
            raise InvalidParameterValue('Layer %s does not support GetFeatureInfo in format %s' %(layerName, format), 'info_format')

        srs = self._getSrsParam(version)
        if srs not in layerObj.crss:
            raise InvalidParameterValue('Layer %s does not support SRS %s' %
                                        (layerName, srs))

        # Convert coordinates to (long, lat) if necessary.
        bbox = self._convertBboxForCrs(bbox, version, srs)

        log.debug("(i,j) (%d,%d)  bbox ((%d,%d)(%d,%d))  crs %s" % (i, j, bbox[0], bbox[1], bbox[2], bbox[3], srs))

        # Translate to geo-coordinates
        x, y = bbox_util.pixelToGeo(i, j, bbox, width, height)

        #start preparing GetFeatureInfo response. Assumes "HTML" output format
#        htmlResponse = "<html><body><p> <b>Feature Information about pixel position: "+self.getOwsParam('i')+","+self.getOwsParam('j')+"/geo position: "+str(x)+","+str(y) +"<b/></p>"
        
        #Adjusts response for multiple layers
#        if len(layers) > 1:
#            htmlResponse = htmlResponse+" Multiple possible features found as follows:"
  
#        htmlResponse = htmlResponse+"<ul>"

        # Dimension handling
        dimValues = {}
        for dimName, dim in layerObj.dimensions.items():
            defaultValue = dim.extent[0]
            dimValues[dimName] = self.getOwsParam(dimName, default=defaultValue)
            log.debug("dimName: %s  dimValue: %s" % (dimName, dimValues[dimName]))

        value = layerObj.getFeatureInfo(format, srs, (x, y), dimValues)
        htmlResponse = (("<table style='width:100%%'><tr><td>Longitude</td><td>%s</td></tr>" +
                         "<tr><td>Latitude</td><td>%s</td></tr>" +
                         "<tr><td>Value</td><td>%s</td></tr></table>")
                        % (str(x), str(y), value))

        response.headers['Content-Type'] = format
        response.write(htmlResponse)

    def GetLegend(self):
        """
        Return an image of the legend.

        """
        # Parameters
        layerName, layerObj = self._getLayerParamInfo()
        format = self._getFormatParam()

        # This hook alows extra arguments to be passed to the layer backend.
        additionalParams = self._getAdditionalParameters(['format'])
        
        dimValues = self._getDimValues(layerObj)
        #now need to revert modified dim values (e.g. height_dim) back to dim values the layerMapper understands (e.g. height)
        restoredDimValues={}
        for dim in dimValues:
            restoredDim=self._mapParamToDim(dim)
            restoredDimValues[restoredDim]=dimValues[dim]
        
        layerObjects = self._getLayerParam()
        styles       = self._getStylesParam(len(layerObjects))        
        
        
        #can't cope with multiple styles so just taking the first one
        if len(styles) > 0:
            style = styles[0]
        else:
            style = None
        
        img = layerObj.getLegendImage(restoredDimValues, 
                                      renderOpts=additionalParams,
                                      style=style)
        
        self._writeImageResponse(img, format)



    def GetInfo(self):
        from pprint import pformat
        request.headers['Content-Type'] = 'text/ascii'
        response.write('Some info about this service\n')
        for layer in model.ukcip02.layers:
            response.write('Layer %s: %s\n' % (layer, pformat(g.ukcip02_layers[layer].__dict__)))

            
    def _getAdditionalParameters(self, expectedParams):
        
        additionalParams = {}
        
        for paramName, paramValue in self._owsParams.items():
            
            paramName = paramName.lower()
                        
            #ignore any of the expected parameters
            if paramName in [p.lower() for p in expectedParams]:
                continue
            
            additionalParams[paramName] = paramValue
            
        return additionalParams
    
    def _getStylesParam(self, numLayers):
        styles = self.getOwsParam('styles', default="")
        
        if styles != "":
            styles = styles.split(',')
            
            assert len(styles) == numLayers, \
               "Number of styles %s didn't match the number of layers %s" % ( len(styles), numLayers)

        return styles

    def _getTransparentParam(self):
        transparent = self.getOwsParam('transparent', default='FALSE')
        return transparent.lower() == 'true'
    
    def _getBgcolorParam(self):
        return self.getOwsParam('bgcolor', default='0xFFFFFF')

    def _getVersionParam(self):
        version = self.getOwsParam('version', default=self.validVersions[0])
        
        if version not in self.validVersions:
            raise InvalidParameterValue('Version %s not supported' % version, 'version')
        
        return version

    def _getSrsParam(self, version):
        if version == '1.1.1':
            srs = self.getOwsParam('srs')
        else:
            srs = self.getOwsParam('crs')
            
        return srs

    def _getBboxParam(self):
        bbox = tuple(float(x) for x in self.getOwsParam('bbox').split(','))
        return bbox
    
    def _getWidthParam(self):
        return int(self.getOwsParam('width'))
    
    def _getHeightParam(self):
        return int(self.getOwsParam('height'))
    

    def _writeImageResponse(self, pilImage, format):
        
        buf = StringIO()
        pilImage.save(buf, self._pilImageFormats[format])

        response.headers['Content-Type'] = format
        
        if config.get('cows.browser_caching_enabled','').lower() == 'true':
            response.headers["cache-control"] = "public, max-age=3600"
            response.headers["pragma"] = ""
                    
        response.write(buf.getvalue())

    def _convertBboxForCrs(self, bbox, version, crs):
        """Convert a bounding box to (min_lon, min_lat, max_lon, max_lat) if necessary depending on
        the WMS version and CRS.
        """
        if (config.get('cows.wms.handleLatLongCoords', 'false').lower() == 'true') and self._isLatLonOrderCrs(version, crs):
            (xmin, ymin, xmax, ymax) = bbox
            return (ymin, xmin, ymax, xmax)
        else:
            return bbox

    def _convertCoordsForCrs(self, coords, version, crs):
        """Convert coordinates to (lon, lat) if necessary depending on the WMS version and CRS.
        """
        if (config.get('cows.wms.handleLatLongCoords', 'false').lower() == 'true') and self._isLatLonOrderCrs(version, crs):
            (x, y) = coords
            return (y, x)
        else:
            return coords

    def _isLatLonOrderCrs(self, version, crs):
        """Determine whether coordinates are specified in (lat, lon) order depending on the WMS
        version and CRS.
        """
        latLonCrss = ['EPSG:4326']
        return ((version != '1.1.1') and (crs.upper() in latLonCrss))
