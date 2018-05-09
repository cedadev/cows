# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
View classes.

:author: Stephen Pascoe
"""

class GridRenderer(object):
    """A class which converts a Grid object into an image.

    :ivar mimeType: The MIME type of images created by this renderer.
    :ivar varmin: The minimum value on the grid for colourmap calculation.
    :ivar varmax: The maximum value of the grid for colourmap calculation.
    """

    mimeType = NotImplemented
    varmin = NotImplemented
    varmax = NotImplemented

    def renderGrid(self, grid, bbox, width, height):
        """Draw the grid into an image.

        @param grid: The grid to draw
        @param bbox: The bounding box to map grid onto.  This may extend
            beyond the grid's bounds.
        @param width: The image width in pixels.
        @param height: The image height in pixels.
        :return: A PIL.Image object.

        :note: grid is expected to cover the entire longitude range of bbox but may
            not cover all of the latitude range if bbox extends beyond the CRS:84 range.
            In this case the returned image must be padded to enforce the correct
            image size and bbox.
        """
        raise NotImplementedError

    def renderColourbar(self, width, height, isVertical=True):
        """
        @param width: The image width in pixels.
        @param height: The image height in pixels.
        @param isVertical: Boolean selecting orientation.
        :return: A PIL.Image object
        """
        pass
