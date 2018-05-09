# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Refactored model of object to support WMS requests through
ows_server.

Primary goals of this model is to:
 - support multiple dimensions.
 - Allow caching of layer views by dimensions and CRS to mitigate
   the overhead of data retreival and rendering.
 - To hide how layers are actually retrieved and rendered from ows_server.

"""


class ILayer(object):
    """
    An interface representing a WMS layer.

    :ivar title: The layer title.  As seen in the Capabilities document.
    :ivar abstract:  Abstract as seen in the Capabilities document.
    :ivar dimensions: A dictionary of IDimension objects.
    :ivar units: A string describing the units.
    :ivar crss: A sequence of SRS/CRSs supported by this layer.

    :todo: Do we need minValue/maxValue?

    """
    title = abstract = dimensions = units = crss = NotImplemented

    def getBBox(self, crs):
        """
        :return: A 4-typle of the bounding box in the given coordinate
            reference system.

        """
        raise NotImplementedError

    def getView(self, crs, dimValues=None, renderOpts={}):
        """
        Creates a view of the layer in a particular CRS and set of
        dimensions.

        @param crs: The coordinate reference system.
        @param dimValues: A mapping of dimension names to dimension values
            as specified in the IDimension.extent
        @param renderOpts: A generic mapping object for passing rendering
            options
        :return: An object implementing ILayerView

        """
        raise NotImplementedError
    


class IDimension(object):
    """
    :ivar units: The units string
    :ivar extent: The extent string

    """
    units = extent = NotImplemented

class ILayerView(object):
    """
    An interface representing a particular view of a WMS layer.

    ILayerView objects are designed to be convenient to cache.
    They should be pickleable to enable memcached support in the future.

    :ivar layer: The source ILayer instance.
    :ivar CRS: The coordinate reference system.
    :ivar dimValues: A mapping of dimension values of this view.
    :ivar renderOpts: The renderOpts used to create this view.
    :ivar bbox: The bounding box as a 4-tuple.

    """
    layer = CRS = dimValues = renderOpts = bbox = NotImplemented

    def getImage(self, bbox, width, height):
        """
        Create an image of a sub-bbox of a given size.

        :ivar bbox: A bbox 4-tuple.
        :ivar width: width in pixels.
        :ivar height: height in pixels.
        :return: A PIL Image object.

        """
        raise NotImplementedError

    def getCacheKey(self):
        """
        Create a unique key for use in caching.

        """
        raise NotImplementedError
