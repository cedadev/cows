# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
implementation of ILayerMapper, IwmsLayer, IwmsDimension, ILayerSlab interfaces, as defined in wms_iface.py & wxs_iface.py

"""
import os, string
import csml
try:
    import cdms2 as cdms
except:
    import cdms
from cows.service.imps.csmlbackend.config import config
try: 
    from PIL import Image, ImageFont, ImageDraw
except ImportError:
    import Image, ImageFont, ImageDraw
from copy import copy
from cows.service.imps.pywms.render_imp import RGBARenderer
from matplotlib import cm
import cdtime
import logging
log = logging.getLogger(__name__)
import numpy

from cows.service.wms_iface import IwmsLayer, IwmsDimension, IwmsLayerSlab
from cows.service.imps.csmlbackend.csmlcommon import CSMLLayerMapper, CSMLConnector

try:
    from PIL import Image
except:
    import Image
from cows import bbox_util

DEFAULT_STYLE=''

class Old_CSMLwmsLayerMapper(CSMLLayerMapper):
    """
    Map keyword arguments to a collection of layers.
    Supports the retrieval of sets of layers according to arbitrary
    keyword/value pairs.
    Implements  ILayerMapper 
    
    """
    def __init__(self):
        super(Old_CSMLwmsLayerMapper, self).__init__()
    
    #!TODO: (spascoe) Could be _getInfo() to make it clear it's internal
    def getInfo(self, feature):
        ''' given a csml feature, return info about the layer/feature
        :return:   title, abstract, dimensions, units, crss '''

        title, abstract = super(Old_CSMLwmsLayerMapper, self).getInfo(feature)
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
       
        
      
    def map(self, **kwargs):
        """
        Given csml.parser.Dataset object list the names of
        all layers available.
        
        :return: A mapping of layer names to ILayer implementations.
        @raise ValueError: If no layers are available for these keywords. 
        """
        fileoruri=kwargs['fileoruri']
        if fileoruri in self.layermapcache.keys():
            #we've accessed this layer map before, get it from the cache dictionary
            return self.layermapcache[fileoruri]
         
        ds = self.connector.getCsmlDoc(fileoruri)
        
        layermap={}
        
        self._crscat=csml.csmllibs.csmlcrs.CRSCatalogue()
        
        for feature in csml.csmllibs.csmlextra.listify(ds.featureCollection.featureMembers):
            
            title, abstract, dimensions, units, crss=self.getInfo(feature)
            
            layermap[feature.id]=CSMLwmsLayer(title,abstract, dimensions, units, crss, feature,
                                              name=feature.id)
        if len(layermap) > 0:
            self.layermapcache[fileoruri]=layermap
            return layermap
        else:
            raise ValueError


class CSMLwmsLayer(IwmsLayer):
    """
     representing a WMS layer.    Implements IwmsLayer

    :ivar title: The layer title.  As seen in the Capabilities document.
    :ivar abstract:  Abstract as seen in the Capabilities document.
    :ivar dimensions: A dictionary of IDimension objects.
    :ivar units: A string describing the units.
    :ivar crss: A sequence of SRS/CRSs supported by this layer.

    :todo: Do we need minValue/maxValue?

    """
    
    def __init__(self, title, abstract, dimensions=None, units=None, crss=None,
                 name=None, dataReader=None, childLayers=None, boundingBox=None):
        self.featureInfoFormats=None #NotImplemented
        self.title=title
        self.name = name
        self.abstract=abstract
        self.dimensions=dimensions
        self.units=units
        self.crss=crss
        
        self.dataReader = dataReader
        
        if childLayers is None:
            self.childLayers = []
        else:
            self.childLayers = childLayers
                
        self.legendSize=(630,80)
        self._minval=0
        self._maxval=10.0 #dummy values
        
        if boundingBox is not None:
            bb=boundingBox

            #convert 0 - 360 to -180, 180 as per common WMS convention
            if abs(bb[2]-bb[0]) >= 359 and abs(bb[2]-bb[0]) < 361:
                bb[0], bb[2]=-180, 180
                
            self.wgs84BBox = bb

            try:
                self.wgs84BBox = self.getBBox('EPSG:4326')
            except:
                raise ValueError("Layer must provide a bounding box in EPSG:4326 "
                                 "coordinates for compatibility with WMS-1.3.0")
                
        self.featureInfoFormats = ['text/html']
        self.featureinfofilecache={} #used for caching netcdf file in getFeatureInfo
        
    def getBBox(self, crs):
        """
        :return: A 4-typle of the bounding box in the given coordinate
            reference system.
        """
        #bb= self._feature.getCSMLBoundingBox().getBox()
        #convert 0 - 360 to -180, 180 as per common WMS convention
        #if abs(bb[2]-bb[0]) >= 359 and abs(bb[2]-bb[0]) < 361:
        #    bb[0], bb[2]=-180, 180
        #self.wgs84BBox = bb
        return self.wgs84BBox
        #raise NotImplementedError
        
    def getSlab(self, crs, style, dimValues, transparent, bgcolor, additionalParams={}):
        """
        Creates a slab of the layer in a particular CRS and set of
        dimensions.

        @param crs: The coordinate reference system.
        @param dimValues: A mapping of dimension names to dimension values
            as specified in the IDimension.extent
        @param renderOpts: A generic mapping object for passing rendering
            options
        :return: An object implementing ILayerSlab
        #create netcdf for whole lat/lon for given dimValues, use to init slab
        """

        var = self.dataReader.getNetcdfVar(self.title, dimValues)
        
        bbox=self.getBBox(crs)
        slab = CSMLwmsLayerSlab(var, self, crs, dimValues, additionalParams, bbox)
        self._minval=slab.minval #needed for legend rendering.
        self._maxval=slab.maxval
        return slab
        
    def getCacheKey(self, crs, style, dimValues, transparent, bgcolor, 
                    additionalParams={}): 
        """
        Create a unique key for use in caching a slab.

        The intention here is that most of the work should be done when
        instantiating an ILayerSlab object.  These can be cached by the
        server for future use.  The server will first call getCacheKey()
        for the slab creation arguments and if the key is in it's cache
        it will use a pre-generated ILayerSlab object.

        """

        dimList = list(dimValues.items())
        dimList.sort()

        #set the default style if none provided
        s = self._getActualStyle(style)
            
        return '%s:%s:%s:%s:%s:%s:%s' % (self.name, crs, s, dimList,
                                      transparent, bgcolor, additionalParams)

    def _getActualStyle(self, style=None):
        actualStyle = None
        
        if style == 'default' or style == '' or style is None:
            actualStyle = DEFAULT_STYLE
        else:
            actualStyle = style
                     
        return actualStyle
    

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
        :return: A string containing the response.

        """
        
        netcdf = self.dataReader.getNetcdfVar(self.title, dimValues)
       
        #Now grab the netCDF object for the point specified.
        #The reason for the 'cob' option is so that if the grid the data 
        #is defined on does not have a grid point at the point specified, 
        #we should  still get the nearest location
        
        t_point = netcdf(latitude=(point[1], point[1], 'cob'), longitude=(point[0], point[0], 'cob'))
        #now get the value recorded at this location
        value = t_point.getValue().tolist()
        log.debug(value)
        log.debug(t_point.fill_value())
        #and the fill_value too
        fill_value = t_point.fill_value()
        #value is actually embedded in a multi dimensional list, 
        #so we need to extract the actual value from the list
        while type(value) is list:
                value = value[0]

        #now check if the value is actually the fill_value rather than 
        #a value recorded at the point specified
        log.debug('%s %s' % (value, fill_value))
        if (2*fill_value) == value:
                value = "No value found at position: "+str(point[1])+", "+str(point[0])
        else:
                value = "Value found at position: "+str(point[1])+", "+str(point[0])+" is: "+str(value)
                
        # finally return the value
        return value

    def getLegendImage(self, dimValues, orientation='horizontal', renderOpts={}
                       , style=None):
        """
        Create an image of the colourbar for this layer.
        @param orientation: Either 'vertical' or 'horizontal'
        :return: A PIL image with labels 

        """
        width = self.legendSize[0]
        height = self.legendSize[1]
        # if width and height specified in the GetLegend request parameters
        # then use them instead of the default values
        if 'width' in renderOpts:
                width = renderOpts['width']
        if 'height' in renderOpts:
                height = renderOpts['height']
                
        cmap = cm.get_cmap(config['colourmap'])
        renderer=RGBARenderer(self._minval, self._maxval)
        
        log.debug("dimValues = %s" % (dimValues,))

        if orientation =='vertical':
            legendImage= renderer.renderColourbar(630, 30, cmap, isVertical=True)
        else:
            legendImage= renderer.renderColourbar(630, 30, cmap, isVertical=False)       
        imageWithLabels=Image.new('RGBA', (630, 80), "white")
        imageWithLabels.paste(legendImage, (0,0))
        #add minvalue label
        minvalueImg=self._simpletxt2image(str(self._minval), (49,25))
        imageWithLabels.paste(minvalueImg,(0,40))
        #add midvalue  label
        midvalue=self._minval+(self._maxval-self._minval)/2
        #add maxvalue label
        midvalueImg=self._simpletxt2image(str(midvalue),(49,25))
        imageWithLabels.paste(midvalueImg,(280,40))
        #add maxvalue label
        maxvalueImg=self._simpletxt2image(str(self._maxval), (49,25))
        imageWithLabels.paste(maxvalueImg,(575,40))
        #add units:
        unitsImg=self._simpletxt2image('Units of measure: %s'%str(self.units), (200,25))
        imageWithLabels.paste(unitsImg,(240,60))     
#        return imageWithLabels                         
        return imageWithLabels.resize((width, height)) 
    
    def _simpletxt2image(self, text, size):
        image = Image.new('RGBA',size,"white")
        fontfullpath = config['legendfont']
        ifo = ImageFont.truetype(fontfullpath,16)
        draw = ImageDraw.Draw(image)
        draw.text((0, 0), text, font=ifo,fill=(100, 123, 165))
        return image
 
    
    
    
class CSMLwmsDimension(IwmsDimension):
    """
    implements IDimension
    :ivar units: The units string.
    :ivar extent: Sequence of extent values.

    """
    
    def __init__(self, domain, dimname, unit):
        self.units = unit
        self.extent = []
        #patch to handle current limitations of multiple time dimension scanning in csml. 
        if string.lower(self.units)[:10] in ['days_since', 'seconds_si', 'minutes_si', 'hours_sinc','months _sin', 'years_sinc']:
            if type(domain[dimname][0]) is not str   :
                tunits=self.units.replace('_', ' ')
                for val in domain[dimname]:
                    csmltime= csml.csmllibs.csmltime.UDtimeToCSMLtime(cdtime.reltime(float(val), tunits).tocomp())
                    self.extent.append(csmltime)
            else:
                for val in domain[dimname]:
                    self.extent.append(str(val))
        else:
            for val in domain[dimname]:
                self.extent.append(str(val))
        #for time axis replace units with iso string
        if dimname == 'time':
            self.units='ISO8601'
       
class CSMLwmsLayerSlab(IwmsLayerSlab):
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

    def __init__(self, var, layer, crs, dimValues, renderOpts, bbox):
        self._var=var
        self.layer = layer
        self.crs = crs
        self.dimValues = dimValues
        self.renderOpts=renderOpts
        self.bbox=bbox
        
        #set colour map for ALL images from this slab
        tvar=var(squeeze=1)
        
        #get the min and max values to use for the colourmapping.
        #change the fill values to ensure they aren't picked up as false max/mins.
        tvar.missing_value=999999999
        value=tvar.getValue()
        self.minval=min(min(l) for l in value)
        tvar.missing_value=-0.000000001
        value=tvar.getValue()
        self.maxval=max(max(l) for l in value)

    def getImage(self, bbox, width, height):
        """
        Create an image of a sub-bbox of a given size.

        :ivar bbox: A bbox 4-tuple.
        :ivar width: width in pixels.`  
        :ivar height: height in pixels.
        :return: A PIL Image object.

        """


        lbbox = self.layer.getBBox(self.crs)
        ibbox = bbox_util.intersection(bbox, lbbox)
    
        log.debug('bbox = %s' % (bbox,))
        log.debug('lbbox = %s' % (lbbox,))
        log.debug('ibbox = %s' % (ibbox,))
    
        # If bbox is not within layerObj.bbox then we need to calculate the
        # pixel offset of the inner bbox, request the right width/height
        # and paste the image into a blank background
        if bbox == ibbox:
            img = self._renderImage(bbox, width, height)
            log.debug('image.size = %s' % (img.size,))
                   
        else:
           
            ix0, iy0 = bbox_util.geoToPixel(ibbox[0], ibbox[3], bbox, width, height,
                                            roundUpY=True)
            ix1, iy1 = bbox_util.geoToPixel(ibbox[2], ibbox[1], bbox, width, height,
                                            roundUpX=True)
            iw = ix1-ix0
            ih = iy1-iy0
            log.debug('Deduced inner image: %s, (%d x %d)' % ((ix0, iy0, ix1, iy1), iw, ih))
            img1 = self._renderImage(ibbox, iw, ih)

            img = Image.new('RGBA', (width, height))
            img.paste(img1, (ix0, iy0))
                    
        return img


    def _renderImage(self, bbox, width, height):
        log.debug('_renderImage(%s, %s, %s)' % (bbox, width, height))
        
        cmap = cm.get_cmap(config['colourmap'])

        grid=Grid(self.layer, self._var, bbox, width, height)
        #If there is no data for the requested area, return a blank image:
        #TODO this should be included in the overhauled rendering code
        if grid.ok ==False:
            width=abs(width)
            height=abs(height)
            img = numpy.empty((width,height),numpy.uint32)
            img.shape=height, width
            pilImage = Image.frombuffer('RGBA',(width,height),img,'raw','RGBA',0,1)
            return pilImage
        #how to handle varmin,varmax? ..read array?
        #minval, maxval=genutil.minmax(grid.value)
        #minval=min(min(l) for l in grid.value)
        #maxval=max(max(l) for l in grid.value)
        minval=self.minval
        maxval=self.maxval
        renderer=RGBARenderer(minval, maxval)         
        return renderer.renderGrid(grid, bbox, width, height, cmap)
    
    
class Grid(object):
    """A class encapsulating a simple regularly spaced, rectilinear
    grid.  This is the only type of grid pywms is expected to
    understand and adaptors should be provided to connect to
    underlying implementations such as cdms or csml.

    :cvar crs: Coordinate reference system

    :ivar x0: coordinate of the lower left corner.
    :ivar y0: coordinate of the lower left corner.
    :ivar dx: The x grid spacing.
    :ivar dy: The y grid spacing.
    :ivar nx: The number of x grid points.
    :ivar ny: The number of y grid points.
    :ivar value: A masked array of the grid values.
    :ivar ix: The dimension index of longidude in value
    :ivar iy: The dimension index of latitude in value
    :ivar long_name: The name of the field.
    :ivar units: The units of the field.
    """
    def __init__(self, layer, var, bbox, width, height):
        #we know the axes are called latitude and longitude as the CSML code has written it:
        v=var  
        
        #sometimes these dimensions get squeezed out so need to get hold of the dx, dy spacing before the variable is subsetted.
        lat=v.getLatitude()
        lon=v.getLongitude()
        self.dx=abs(lon[0]-lon[1])
        self.dy=abs(lat[0]-lat[1])
        self.long_name=v.id
        self.units=v.units
        #now do the subset.
        try:
            tvar=v(latitude=(bbox[1], bbox[3]), longitude=(bbox[0],bbox[2]),squeeze=1)     
            if type(tvar) == numpy.float32:
                order ='xy'
                self.value=numpy.ndarray(tvar)
                self.ix=0
                self.iy=1
                self.x0=bbox[0]
                self.y0=bbox[1]
                self.nx=self.ny=1
            else:    #it's a transient variable.
                order=tvar.getOrder()
                #array of data
                self.value=tvar.getValue()
                if order == 'xy':
                    self.ix=0
                    self.iy=1
                else:
                    self.ix=1
                    self.iy=0
                lat = tvar.getLatitude()
                lon = tvar.getLongitude()      
                if lon is not None:
                    self.x0=lon[0]
                    self.nx=len(lon)
                else: #it's a single longitude value
                    self.x0=bbox[0]
                    self.nx= 1      
                if lat is not None:
                    self.y0=lat[0]
                    self.ny=len(lat)
                else: #it's a single latitude value
                    self.y0=bbox[1]
                    self.ny= 1
                self.ok=True #the grid is correctly initialised
        except cdms.CDMSError:
            self.ok=False #the grid failed due to a cdms error (most likely data not available for bounding box)
            
        
