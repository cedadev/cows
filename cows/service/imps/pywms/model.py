# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Model classes.

:author: Stephen Pascoe
"""

### Not needed within Pylons
##
## class WebMapService(object):
##     """
##     :ivar title: The service title.  Inserted into GetCapabilities.
##     :ivar layers: A mapping of layer names to Layer objects.
##     :ivar layerFolder: A LayerFolder instance describing the layer heirarchy.
##     :ivar version: The WMS version string.
##     :ivar crs: The default coordinate reference system
##     :ivar bbox: the default bounding box
##     """


##     def __init__(self, title):
##         self.title = title
##         self.layers = {}
##         self.layerFolder = LayerFolder(title)
##         self.version = '1.3.0'
##         self.crs = 'CRS:84'
##         self.bbox = '-180,-90,180,90'


class Layer(object):
    """
    :ivar title: The layer title.  Inserted into GetCapabilities.
    :ivar abstract: The Layer abstract.  Inserted into GetCapabilities
    :ivar dimensions: A dictionary of dimension objects.
    :ivar minValue: The minumum value of the layer for colourbar calculation.
    :ivar maxValue: The maximum value of the layer for colourbar calculation.
    :ivar units: A string describing the units.
    :ivar crs: Base Spatial/Coordinate reference system of the layer
    """
    
    def __init__(self, title, abstract=None):
        self.title = title
        self.abstract = abstract
        self.dimensions = {}

    def selectGrid(self, bbox, dimensionSpec):
        """
        @param bbox: A 4-tuple of the bounding box.
        @param dimensionSpec: A mapping of dimension name to value.
        :return: A Grid instance of shape covering
            the requested bounding box and dimension specification.

        :note: The bbox may lie outside the CRS:84 range in both latitude and longitude
            (for compatibility with OpenLayers).  In this case the returned grid must
            cover the entire longitude range but may only cover the part of the latitude
            range which overlaps with CRS:84.
        @see: view.GridRenderer for constraints expected on the returned Grid.
        """
        raise NotImplementedError

    def describe(dimensionSpec):
        """
        @param dimensionSpec: A mapping of dimension name to value.
        :return: A string describing the layer selection.
        """
        raise NotImplementedError

### Not needed for within Pylons
##
## class LayerFolder(object):
##     """A class to build heirarchies of layers.

##     Layer folders contain subfolders or names of layers.

##     :ivar name: The layer name or None
##     :ivar title: The layer title.  Inserted into GetCapabilities.
##     :ivar abstract: The Layer abstract.  Inserted into GetCapabilities.
##     :ivar contents: A list of LayerFolders or strings naming layers

##     """
##     def __init__(self, title, name=None, abstract=None):
##         self.title = title
##         self.name = name
##         self.abstract = abstract
##         self.contents = []

##     def iterSubFolders(self):
##         """Iterate over subfolders, avoiding leaves.

##         """
##         for item in self.contents:
##             if type(item) != str:
##                 yield item

##     def iterLeaves(self):
##         """Iterate over leaves, avoiding subfolders.

##         """
##         for item in self.contents:
##             if type(item) == str:
##                 yield item
    

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

    crs = NotImplemented

    x0 = y0 = dx = dy = nx = ny = value = ix = iy = long_name = units = NotImplemented
    
class Dimension(object):
    """
    :ivar units: The units string
    :ivar extent: The extent string
    """

    def __init__(self, name, units, extent=""):
        self.name = name
        self.units = units
        self.extent = extent
    
