# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import time
import numpy
import logging

import geoplot.colour_bar
from geoplot.layer_drawer_grid import LayerDrawerGrid
from geoplot.layer_drawer_grid_fast import LayerDrawerGridFast

from cows.service.imps.geoplot_wms_backend.slabs.slab_base import SlabBase
from cows.service.imps.geoplot_wms_backend.slab_options_parser import SlabOptionsParser
from cows.service.imps.geoplot_wms_backend.rendering_option import RenderingOption

log = logging.getLogger(__name__)

class SlabGrid(SlabBase):

    style = 'grid'
    title = 'Grid Boxes'
                        
    renderingOptions = SlabBase.renderingOptions +[     
        RenderingOption('disable_subset', "Disable Subsetting" ,bool,False),
        RenderingOption('show_grid_lines', "Draw Grid Boxes" ,bool,False),
        RenderingOption('hide_outside', "Mask Data Outside Bounds" , bool ,False),
    ]
        
    def _setupLayerDrawer(self):
                        
        if self.parser.getOption('disable_subset'):
            ldClass = LayerDrawerGrid
        else:
            ldClass = LayerDrawerGridFast
    
        ld = ldClass(self.variable, 
                     cmap=self.parser.getOption('cmap'), 
                     showGridLines=self.parser.getOption('show_grid_lines'),
                     colourBarMin=self.parser.getOption('cmap_min'),
                     colourBarMax=self.parser.getOption('cmap_max'),
                     colourBarScale = self.parser.getOption('cmap_scale'),
                     hideOutside = self.parser.getOption('hide_outside'),
                     bgcolor = self.bgcolor,
                     transparent=self.transparent,
                     drawIntervals=False,)
        
        return ld
    
    @classmethod
    def makeColourBar(cls, width , height, orientation, units, renderOpts, variable):
        parser = SlabOptionsParser(SlabGrid.renderingOptions, renderOpts)
        log.debug('makeColourBar renderopts %s'%renderOpts)
        minval = parser.getOption('cmap_min')
        if minval == None:
            minval = variable.min()
            
        maxval = parser.getOption('cmap_max')
        if maxval == None:
            maxval = variable.max()
            
            # can't have a colourbar with an infinite maximum, take the highest 
            # non-inf value.
            if maxval == numpy.inf:
                maxval = numpy.ma.masked_equal(variable, numpy.inf).max()

        # Check for non-default, but valid, colour map.
        cls._setUpColourMap(renderOpts.get('cmap', None))

        im = geoplot.colour_bar.getColourBarImage(width, height, 
                                             label='Units of measure: %s' % str(units),
                                             cmap=parser.getOption('cmap'), 
                                             colourBarMin=minval,
                                             colourBarMax=maxval,
                                             colourBarScale=parser.getOption('cmap_scale'), 
                                             orientation=orientation,
                                             colourBarStyle='continuous',
                                             )
    
        return im    
