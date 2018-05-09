# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Implementation of grid rendering classes.

@author: Stephen Pascoe
"""

from view import GridRenderer
try: 
    from PIL import Image, ImageColor
except ImportError:
    import Image, ImageColor

import numpy as N
import logging
from matplotlib import cm, colors

logger = logging.getLogger(__name__)

class RGBARenderer(GridRenderer):
    """Creates an RGBA PNG with a selectable matplotlib colour scale.
    """

    mimeType = 'image/png'

    def __init__(self, varmin, varmax):
        self.varmin = varmin
        self.varmax = varmax
        self._norm = colors.normalize(varmin, varmax)

    def renderColourbar(self, width, height, cmap, isVertical=True):
        a = N.arange(0, 1.0, 1.0/256)
        if isVertical:
            a = a[-1::-1]
            shape = (1, 256)
        else:
            shape = (256, 1)
        cbar = (cmap(a) * 255).astype('b').tostring()
        img = Image.frombuffer("RGBA", shape, cbar, "raw", "RGBA", 0, 1)
        img = img.resize((width, height))
        return img

    def renderGrid(self, grid, bbox, width, height, cmap):
        cmap.set_bad('#ffffff', 0.0)

        logger.debug('grid %s, %s, %s, %s, %s, %s, %s, %s' %
                    (grid.x0, grid.y0, grid.dx, grid.dy, grid.nx, grid.ny,
                     grid.ix, grid.iy))
#        logger.debug('bbox %s' % (bbox,))
#        logger.debug('width %s'%width)
#        logger.debug('height %s'%height)

        # Get a pixel = grid-box image for the grid
        img = self._grid2Img(grid, cmap)

        logger.debug('image size%s' %str(img.size))
        # Calculate the pixel-size of a grid box
        
        
        numDeg_X=grid.dx*grid.nx
        numDeg_Y=grid.dy*grid.ny
        pxPerDeg_x=float(width)/numDeg_X
        pxPerDeg_y=float(height)/numDeg_Y
# modified from this: 
#        pxPerDeg_x = float(width) / (bbox[2] - bbox[0])
#        pxPerDeg_y = float(height) / (bbox[3] - bbox[1])
        pxPerGrid_x = grid.dx * pxPerDeg_x
        pxPerGrid_y = grid.dy * pxPerDeg_y

        # Scale Img to the right size
        logger.debug('resizing to %s in X and %s in y'%(abs(pxPerGrid_x * grid.nx),abs(pxPerGrid_y * grid.ny)))
        img = img.resize(((abs(pxPerGrid_x * grid.nx),
                           abs(pxPerGrid_y * grid.ny))))
        #!NO: We assume the grid points represent the centre of the grid boxes
        #!NO: therefore we can calculate the upper-left position of the image
        # Adapted so that the grid points represent the lower left corner of grid boxes

#        
#        
#        # Find top-left corner of grid
#        if grid.dx > 0:
#            leftX = grid.x0
#        else:
#            leftX = grid.x0 + (grid.dx * (grid.nx - 1))
#        if grid.dy > 0:
#            topY = grid.y0 + (grid.dy * (grid.ny - 1))
#        else:
#            topY = grid.y0
#
#        logger.debug('top-left = %s x, %s y' % (leftX, topY))
#
#        # Find pixel position of top left centre grid box
#        cx = width * ((leftX - bbox[0])/ (bbox[2] - bbox[0]))
#        cy = height * ((bbox[3] - topY) / (bbox[3] - bbox[1]))
#        logger.debug('top-left centre pixel = %s x, %s y' % (cx, cy))
#
#        # Apply half width of grid box
#        ox = int(cx - pxPerGrid_x / 2)
#        oy = int(cy - pxPerGrid_y / 2)
##        ox,oy = int(cx), int(cy-pxPerGrid_y)
#        logger.debug('Offset: %s x, %s y' % (ox, oy))


        # Paste the grid image into the tile image
        tileImg = Image.new('RGBA', (width, height))
        #logger.debug('Pasting image img%s into tileImg%s at (%s,%s)' % (img.size, tileImg.size, ox, oy))
#        tileImg.paste(img, (ox, oy))
        tileImg.paste(img, (0,0))
        return tileImg
    


    def _grid2Img(self, grid, cmap):
        """Returns the grid as an image where each pixel is one grid box.
        """
        a = self._norm(grid.value)
        
        img_buf = (cmap(a) * 255).astype('b')
        # This code assumes the axis ordering is either (y, x, time) or (x, y, time)
        if min(grid.iy, grid.ix) != 0 and max(grid.iy, grid.ix) != 1:
            raise ValueError("X and Y must be the first 2 dimensions!")
        if grid.iy < grid.ix:
            yxOrdering = True
        else:
            yxOrdering = False
            
        #fix for extreme zoom errors  
        try:
            img = Image.frombuffer("RGBA", img_buf.shape[1::-1], img_buf.tostring(), "raw", "RGBA", 0, 1)
        except ValueError:
            if len(grid.value.shape) == 1: 
                imageshape=(grid.value.shape[0], 1)    
                img = Image.frombuffer("RGBA", imageshape, img_buf.tostring(), "raw", "RGBA", 0, 1)
#        img.save('/tmp/raw1.png')

        # Rotate if axis order is x, y
        if not yxOrdering:
            img = img.transpose(Image.ROTATE_90)
        # Flip if x or y are ordered the wrong way
        if grid.dy > 0:
            logger.debug('Flipping y')
            img = img.transpose(Image.FLIP_TOP_BOTTOM)
        if grid.dx < 0:
            logger.debug('Flipping x')
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        return img

