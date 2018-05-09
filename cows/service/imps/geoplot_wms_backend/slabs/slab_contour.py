# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import logging
import time
import numpy

import geoplot.colour_bar
from geoplot.layer_drawer_contour import LayerDrawerContour

from cows.service.imps.geoplot_wms_backend.slabs.slab_base import SlabBase
from cows.service.imps.geoplot_wms_backend.slab_options_parser import SlabOptionsParser
from cows.service.imps.geoplot_wms_backend.rendering_option import RenderingOption

log = logging.getLogger(__name__)

class SlabContour(SlabBase):

    style = 'contour'
    title = 'Contour Lines'
                      
    renderingOptions = SlabBase.renderingOptions + [       
        RenderingOption('num_contour_lines', "Number of Contour Lines" ,int,10),
        RenderingOption('contour_font_size', "Contour Label Size" ,str,'medium',["small","medium", "large",]),
        RenderingOption('contour_label_interval', "Interval Between Labels" ,int,1),
        RenderingOption('intervals', "Contour Lines" ,str, None),
    ]

    def _setupLayerDrawer(self):
        
        ld = LayerDrawerContour(self.variable, 
                                 cmap=self.parser.getOption('cmap'), 
                                 colourBarMin=self.parser.getOption('cmap_min'),
                                 colourBarMax=self.parser.getOption('cmap_max'),
                                 bgcolor = self.bgcolor,
                                 colourBarScale = self.parser.getOption('cmap_scale'),
                                 labelInterval= self.parser.getOption('contour_label_interval'),
                                 numLines = self.parser.getOption('num_contour_lines'),
                                 fontSize = self.parser.getOption('contour_font_size'),
                                 intervals = self.parser.getOption('intervals'),
                                 transparent=self.transparent)
        
        return ld


    @classmethod
    def makeColourBar(cls, width , height, orientation, units, renderOpts, variable):
        
        parser = SlabOptionsParser(SlabContour.renderingOptions, renderOpts)
        minval = parser.getOption('cmap_min')
        log.debug('setting minval as %s'%minval)
        if minval == None:
            minval = variable.min()
            log.debug('setting minval as variable min%s'%minval)
            
        maxval = parser.getOption('cmap_max')
        log.debug('setting maxval as %s'%maxval)
        if maxval == None:
            maxval = variable.max()
            log.debug('setting maxval as variable max%s'%maxval)    
            # can't have a colourbar with an infinite maximum, take the highest 
            # non-inf value.
            if maxval == numpy.inf:
                log.debug(' maxval equals numpy infinite')
                maxval = numpy.ma.masked_equal(variable, numpy.inf).max()
        log.debug('intervals %s'%repr(parser.getOption('intervals')))

        # Check for non-default, but valid, colour map.
        cls._setUpColourMap(renderOpts.get('cmap', None))

        im = geoplot.colour_bar.getColourBarImage(width, height, 
                                             label='Units of measure: %s' % str(units),
                                             cmap=parser.getOption('cmap'), 
                                             colourBarMin=minval,
                                             colourBarMax=maxval,
                                             colourBarScale=parser.getOption('cmap_scale'),
                                             numIntervals=parser.getOption('num_contour_lines') - 1, 
                                             orientation=orientation,
                                             intervals=parser.getOption('intervals'),
                                             colourBarStyle='line',
                                             )
    
        return im
