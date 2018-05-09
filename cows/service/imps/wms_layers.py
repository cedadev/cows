# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
implementation of ILayerMapper, ILayer, IDimension, ILayerSlab interfaces, as defined in wms_iface.py
this implementation was written to read station data.
"""
import os
import cdms2 as cdms
try: 
    from PIL import Image
except ImportError:
    import Image
from copy import copy
from pointrenderer import PointRenderer
from matplotlib import cm
import genutil
#!FIXME: modules in the service package shouldn't depend on pylons!
from pylons import config  #config must have tmpfilebuffer and csmlstore values
from layers import LayerParser
from csml2kml.utils import wget
from StationCollection import StationCollection
from xml.etree.ElementTree import ElementTree, Element, SubElement, XML
import urllib
from matplotlib import dates 

from cows.service.wxs_iface import ILayerMapper
from cows.service.wms_iface import IwmsLayer, IwmsDimension, IwmsLayerSlab

import logging
log = logging.getLogger(__name__)

class WMSLayerMapper(ILayerMapper):
    """
    Map keyword arguments to a collection of layers.
    Supports the retrieval of sets of layers according to arbitary
    keyword/value pairs.
    Implements  ILayerMapper 
    
    """
    def __init__(self):
    
        """
        Lists the names of all layers available as listed in the configuration file specified by the 'layer_config' parameter in the development.ini file.

        :return: A mapping of layer names to ILayer implementations.
        @raise ValueError: If no layers are available for these keywords.
        """
        
        filename=config['layer_config']
        if not os.path.exists(filename):
            raise Exception(str('Config File could not be found: %s')%filename)
        log.debug('Initialising WMS layermapper from %s' % filename)
        
        #instantiate LayerParser class with the value of 'layer_config' as parameter to read layer infromation
        layerparser = LayerParser(filename)

        layermap={}
        layers = layerparser.getLayers()
        for feature in layers:
            # read information necessary to create a StationLayer object
            title, abstract, crss,formats, serverURL, icon, featureName, dataSet, bbox, dataSetURL =self._getInfo(feature)
            # URL required to query the relevant WFS server to acquire a list of station for the current layer in the loop
            geoServerUrl =serverURL+'/wfs?request=getfeature&service=wfs&version=1.1.0&typename='+featureName+'&maxfeatures=100'
            log.debug('Geoserver URL: %s' % geoServerUrl)
            geoServerResponse = wget(geoServerUrl)
            stationCollection=StationCollection(geoServerResponse)
            # specify the filepath for the static image to be used for representing each station in the GetMap image
            icon =config['csml_config']+'/img/'+icon
            log.debug('icon: %s' % icon)
            #instantiate a StationLayer object and store that in the layermap dictionary with the name of the layer as the key
            layermap[feature.findtext("Name")]=StationLayer(title,abstract, crss, stationCollection,bbox, formats, icon, dataSet, dataSetURL)
        if len(layermap) > 0:
            self.layermap = layermap
        else:
            raise ValueError

    
    def _getInfo(self, feature):
        ''' given a Station feature, return info about the layer/feature
        :return:    title, abstract, crss, formats, serverURL, icon, featureName,dataSet, bbox, dataSetURL  '''

        try:
            title=feature.findtext("Title")
        except:
            title=''
        try:
            abstract=feature.findtext("Abstract")
        except:
            abstract=title
        
        crs=feature.findtext("SRS")
        crss=[crs]
        log.debug('crss: %s' % crss)
        formats = []
        
        #read supported getFeatureInfo formats from the "SupportedFormats" element
        sFElem = feature.getchildren()[4]
        for format in sFElem.getchildren():
                formats.append(format.text)
        
        # read orignal bbox info
        bboxElem = feature.getchildren()[5]
        bbox=[int(bboxElem.getchildren()[0].text),int(bboxElem.getchildren()[1].text),int(bboxElem.getchildren()[2].text),int(bboxElem.getchildren()[3].text)]
        #static image to be used for GetMap response
        icon = feature.getchildren()[6].text
        #read WFS server information
        wfsElem = feature.getchildren()[7]
        serverURL = wfsElem.getchildren()[0].text
        featureName = wfsElem.getchildren()[1].text
        dataSet = wfsElem.getchildren()[2].text
        dataSetURL =  wfsElem.getchildren()[3].text
        return title, abstract, crss, formats, serverURL, icon, featureName,dataSet, bbox, dataSetURL



   
    def map(self, **kwargs):
        '''this function is called by the wms_controller class to acquire information about all available layers'''
        return self.layermap


class StationLayer(IwmsLayer):
    """
    representing a WMS layer for MIDAS/ECN Stations.    Implements ILayer

    :ivar title: The layer title.  As seen in the Capabilities document.
    :ivar abstract:  Abstract as seen in the Capabilities document.
    :ivar crss: A sequence of SRS/CRSs supported by this layer.
    :ivar stationCollection: A list of NPStation objects to be rendered as part of GetMap response
    :ivar formats: A list of output formats supported by the layer in question for GetFeatureInfo response
    :ivar icon: A static image to be used for representing each station in the stationCollection in the GetMap response
    :ivar dataSet: Name of the dataset to be used to construct an URL for the GetFeatureInfo response
    :ivar dataSetURL: Server address part of the URL to be returned as a part of the GetFeatureInfo response

    """

    def __init__(self, title, abstract, crss, stationCollection, wgs84BBox, formats, icon,dataSet, dataSetURL):        
        self.title=title
        self.abstract=abstract
        self.crss=crss
        self.legendSize=(300,60)
        self.dimensions ={}
        self.stationCollection = stationCollection
        self.featureInfoFormats= formats
        self.wgs84BBox=wgs84BBox
        self.dataSet = dataSet
        self.dataSetURL = dataSetURL
        self.icon = icon
    def getBBox(self, crs):
        """
        :return: A 4-tuple of the bounding box in the given coordinate
            reference system.
        """
        bb= self.wgs84BBox
        #convert 0 - 360 to -180, 180 as per common WMS convention
        if abs(bb[2]-bb[0]) >= 359 and abs(bb[2]-bb[0]) < 361:
            bb[0], bb[2]=-180, 180
        return bb
        #raise NotImplementedError
        
    def getSlab(self, crs, dimValues=None, renderOpts={}):
        """
        Creates a slab of the layer in a particular CRS and set of
        dimensions.

        @param crs: The coordinate reference system.
        @param dimValues: A mapping of dimension names to dimension values
            as specified in the IDimension.extent
        @param renderOpts: A generic mapping object for passing rendering
            options
        :return: An object implementing ILayerSlab
        
        """
        bbox=self.getBBox(crs)
        return StationLayerSlab(self, crs, dimValues, renderOpts, bbox,self.icon, self.stationCollection)
               
    def getCacheKey(self, crs, dimValues=None, renderOpts={}):
        """
        Create a unique key for use in caching a slab.

        The intention here is that most of the work should be done when
        instantiating an ILayerSlab object.  These can be cached by the
        server for future use.  The server will first call getCacheKey()
        for the slab creation arguments and if the key is in it's cache
        it will use a pre-generated ILayerSlab object.

        """
        return None
        #raise NotImplementedError
        
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
        @param dimValues: A mapping of dimension names to dimansion values.
        :return: A string containing the response.
        
        """
        log.debug('Point: %s' % point)
        nearestStation = self.stationCollection.getNearestStation(point[1], point[0])
        
        log.debug('Nearest station: %s' % nearestStation.desc)
        
        
        responseURL = self.dataSetURL+'/list?dataset_id='+self.dataSet+'&station_name='+nearestStation.desc
        # replace space characters in the URL with %20 to avoid any URL validation error on the client side 
        responseURL = responseURL.replace(' ', '%20')
        log.debug('Response URL: %s' % responseURL)
        #finally construct the response, in this case it is in HTML with the responseURL represented as a hyperlink in it
        response = "Description: <em>"+nearestStation.desc+"</em><br /><a href='"+responseURL+"'>"+responseURL+"</a>"
        return response

    def getLegendImage(self, orientation='vertical', renderOpts={}):
        """
        Create an image of the colourbar for this layer.

        @param orientation: Either 'vertical' or 'horizontal'
        :return: A PIL image

        """
        width = self.legendSize[0]
        height = self.legendSize[1]
        # if width and height specified in the GetLegend request parameters
        # then use them instead of the default values
        if 'width' in renderOpts:
                width = renderOpts['width']
        if 'height' in renderOpts:
                height = renderOpts['height']
        renderer=PointRenderer()
        legImage = Image.new('RGBA', (width, height), (0,0,0,0))
        # legend for stations without any associated dataset
        withoutData = Image.open(self.icon)
        # legend for stations that contain datasets
        withData= Image.open(self.icon+'1')
        legImage.paste(withoutData, (0,0))
        legImage.paste(renderer.txt2img(self.title+' without dataset', "helvB08.pil"),(30, 5) )
        legImage.paste(withData, (0, 30))
        legImage.paste(renderer.txt2img(self.title+' with dataset', "helvB08.pil"),(30, 35) )        
        return legImage

class StationDimension(IwmsDimension):
    """
    implements IDimension
    :ivar units: The units string.
    :ivar extent: Sequence of extent values.

    """
    
    def __init__(self, domain, dimname, unit):
        self.units = unit
        self.extent = []
        for val in domain[dimname]:
            self.extent.append(str(val))
               
       
        
        
class StationLayerSlab(IwmsLayerSlab):
    """
    Implements LayerSlab
    Represents a particular horizontal slice of a WMS layer.

    ILayerSlab objects are designed to be convenient to cache.
    They should be pickleable to enable memcached support in the future.

    :ivar layer: The source ILayer instance.
    :ivar crs: The coordinate reference system.
    :ivar dimValues: A mapping of dimension values of this view.
    :ivar renderOpts: The renderOpts used to create this view.
    :ivar bbox: The bounding box as a 4-tuple.
    """
    
    def __init__(self,  layer, crs, dimValues, renderOpts, bbox, icon,stationCollection):
        self.layer = layer
        self.crs = crs
        self.dimValues = dimValues
        self.renderOpts=renderOpts
        self.bbox=bbox
        self.stationCollection = stationCollection
        self.icon = icon 
    def getImage(self, bbox, width, height):
        """
        Create an image of a sub-bbox of a given size.

        :ivar bbox: A bbox 4-tuple.
        :ivar width: width in pixels.`  
        :ivar height: height in pixels.
        :return: A PIL Image object.

        """
        log.debug('BBOX: %s' % bbox)
        stationsInBbox = self.stationCollection.getStationsInBBox(bbox[1],bbox[0],bbox[3], bbox[2])
        
        
        cmap=eval(config['colourmap']) 
        renderer=PointRenderer()         
        return renderer.renderPoint(bbox, stationsInBbox, width, height, cmap,self.icon)
