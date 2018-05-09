# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import logging
import time

import numpy

from geoplot.utils import isRangeInLimits
import geoplot.colour_scheme as colour_scheme

from cows.service.wms_iface import IwmsLayerSlab
from cows.service.imps.image_import import Image
from cows.service.imps.geoplot_wms_backend.slab_options_parser import SlabOptionsParser
from cows.service.imps.geoplot_wms_backend.rendering_option import RenderingOption
    
log = logging.getLogger(__name__)

class SlabBase(IwmsLayerSlab):
    """
    A layer slab that implements the IwmsLayerSlab interface and uses geoplot
    to render the required images.
    
    This is an abstract base class and should not be used directly.
    """

    renderingOptions = [
        RenderingOption('cmap', "Colour Scheme" ,str,'jet',["bone","jet", "copper", "gray", "winter"] ),
        RenderingOption('cmap_min', "Legend Min" ,float,None),
        RenderingOption('cmap_max', "Legend Max" ,float,None),
        RenderingOption('cmap_scale', "Colour Bar Scale" ,str ,'linear', ['linear','log']),
    ]

    """
    constructor
    
    @param variable: the netcdf variable that contains the data for this slab
    @param title: the title of the variable that is to be used
    @param crs: the coordinate refrence system the data is stored in
    @param dimValues: the dimension values for this slab
    @param transparent: indicates if the produced image should be transparent or
        not.
    @param bbox: the bounds of the data in lat/lon
    @param renderOpts: the additional parameters recieved by the WMS, may include
        some custom rendering options.
    """
    def __init__(self, variable, title, crs, dimValues, transparent, bgcolor, bbox, renderOpts):

        self.title = title
        self.renderOpts = renderOpts
        self.bgcolor = bgcolor
        self.transparent = transparent
        self.variable = variable
                
        #log.debug("renderOpts = %s" % (renderOpts,))
        
        # Check for non-default, but valid, colour map.
        cmapName = renderOpts.get('cmap', None)
        self._setUpColourMap(cmapName)

        self.parser = SlabOptionsParser(self.renderingOptions, renderOpts)
        self.ld = self._setupLayerDrawer()
    
    @classmethod
    def _setUpColourMap(cls, cmapName):
        """Adds a colour map to those defined in the rendering options if it is valid and not
        present already.
        @param cmapName: name of colour map
        """
        log.debug("Checking for cmap %s" % cmapName)
        cmapOptions = [r for r in cls.renderingOptions if r.name == 'cmap'][0]
        if cmapName not in cmapOptions.options:
            log.debug("Not found in renderingOptions %s" % cmapName)
            if colour_scheme.isValidCmapName(cmapName):
                log.debug("Valid cmap name %s" % cmapName)
                cmapOptions.options.append(cmapName)
        log.debug("All known cmaps %s" % cmapOptions)

    """
    Creates the layer drawer object so that it can be used in getImage
    """
    def _setupLayerDrawer(self):
        raise NotImplementedError()
    
    """
    returns an image of the data constructed using the layer drawer
    
    @param bbox: the limits of the image requested
    @param width: the width in px of the image
    @param height: the height in px of the image
    """
    def getImage(self, bbox, width, height):
        """
        Create an image of a sub-bbox of a given size.

        :ivar bbox: A bbox 4-tuple.
        :ivar width: width in pixels.`  
        :ivar height: height in pixels.
        :return: A PIL Image object.

        """
        #log.debug("GetImage called with bbox=%s, width=%s, height = %s" % (bbox, width, height,))
        
        xLimits = (bbox[0], bbox[2])
        yLimits = (bbox[1], bbox[3])
        
        if sorted(self.variable.getAxisIds()) == sorted(['latitude','longitude']):
            
            if not self._areBoundsInLimits(bbox, xLimits, yLimits):
                
                img = numpy.zeros((height,width,4), numpy.uint8)
                pilImage = Image.fromarray(img, 'RGBA')
                
                log.debug("empty image used as no data found for id=%s (%sx%s), lon=%s, lat=%s " % \
                  (self.variable.id, width, height, xLimits, yLimits))
            
                return pilImage
                       
        st = time.time()
        im = self.ld.makeImage(xLimits, yLimits, width, height)
        
        log.debug("generated contour image id=%s (%sx%s, lon=%s, lat=%s in %.2fs" % \
                  (self.variable.id, width, height, xLimits, yLimits,  time.time() - st,))
        
        return im

    def _areBoundsInLimits(self, bbox, xLimits, yLimits):
        
        if self.variable.getAxisIds()[0] == 'longitude':
            lonAx, latAx = self.variable.getAxisList()
        else:
            latAx, lonAx = self.variable.getAxisList()
            
        xRange = [ lonAx.getBounds().min(), lonAx.getBounds().max()]
        yRange = [ latAx.getBounds().min(), latAx.getBounds().max()]
        log.debug("xLimits = %s" % (xLimits,))
        log.debug("yLimits = %s" % (yLimits,))
        log.debug("xRange = %s" % (xRange,))
        log.debug("yRange = %s" % (yRange,))
        log.debug("x range is circular: %s" % ("True" if lonAx.isCircular() else "False",))

        isInLimits = ((lonAx.isCircular() or isRangeInLimits(xRange, xLimits)) and
                      isRangeInLimits(yRange, yLimits))

        log.debug("isInLimits = %s" % (isInLimits,))
        
        return isInLimits
