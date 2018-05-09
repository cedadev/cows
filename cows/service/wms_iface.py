# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
The classes in this module define an interface between the OWS Pylons
server and components that provide Web Map Server layers. They extend
the interfaces defined in :mod:`cows.service.wxs_iface`.

The interface was designed with several requirements in mind

* support multiple dimensions (in the WMS sense, i.e. non-geospatial dimensions).
* support multiple CRSs/SRSs
* Allow caching of horizontal slices (called layer slabs) by dimensions and CRS to mitigate the overhead of data retreival and rendering.
* To hide how layers are actually retrieved and rendered from ows_server.

IwmsLayer instances provide dimension and CRS information to the server
and can render a legend.  A layer image is requested by a two stage
process.  First the CRS and non-geospatial dimensions are selected
through IwmsLayer to return a IwmsLayerSlab instance.  WMS images are then
retrieved through IwmsLayerSlab for a given bounding box.

This allows implementations to cache the result if it makes sense to
do so.  implementing IwmsLayer.getCacheKey() will cause the server to
cache IwmsLayerSlab objects for future use, therefore not requiring
repeated calls to IwmsLayer.getSlab().  This strategy works well with
tiling WMS clients that will make multiple GetMap requests with the
same CRS and dimension parameters.


"""

from wxs_iface import ILayer

        
#!TODO: missing definitions: self.dimensions
class IwmsLayer(ILayer):
    """
    An interface representing a WMS layer, based on ILayer.
    
    :ivar legendSize: (width, height) in pixels of legend.

    :ivar featureInfoFormats: A sequence of formats supported for the
        self.getFeatureInfo method.  If this is None or empty GetFeatureInfo
        is not supported.

    :todo: Do we need minValue/maxValue?

    """


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
        raise NotImplementedError

    def getCacheKey(self, crs, dimValues=None, renderOpts={}):
        """
        Create a unique key for use in caching a slab.

        Any unique combination of crs, dimValues and renderOpts should
        produce a unique key.

        The intention here is that most of the work should be done when
        instantiating an ILayerSlab object.  These can be cached by the
        server for future use.  The server will first call getCacheKey()
        for the slab creation arguments and if the key is in it's cache
        it will use a pre-generated ILayerSlab object.

        """
        raise NotImplementedError

    def getLegendImage(self, orientation='vertical', renderOpts={}):
        """
        Create an image of the colourbar for this layer.
        
        @param orientation: Either 'vertical' or 'horizontal'
        :return: A PIL image

        """
        raise NotImplementedError

    def getFeatureInfo(self, format, crs, point, dimValues):
        """
        Return a response string descibing the feature at a given
        point in a given CRS.

        @param format: One of self.featureInfoFormats.  Defines which
            format the response will be in.
        @param crs: One of self.crss
        @param point: a tuple (x, y) in the supplied crs of the point
            being selected.
        @param dimValues: A mapping of dimension names to dimansion values.
        :return: A string containing the response.

        """
        raise NotImplementedError
        

class IwmsDimension(object):
    """
    An interface representing a WMS dimension
    
    :ivar units: The units string.
    :ivar extent: Sequence of extent values.

    """
    units = extent = NotImplemented

class IwmsLayerSlab(object):
    """
    An interface representing a particular horizontal slice of a WMS layer.

    IwmsLayerSlab objects are designed to be convenient to cache.
    Ideally they should be pickleable to enable memcached support in
    the future.

    :ivar layer: The source IwmsLayer instance.
    :ivar crs: The coordinate reference system.
    :ivar dimValues: A mapping of dimension values of this view.
    :ivar renderOpts: The renderOpts used to create this view.
    :ivar bbox: The bounding box as a 4-tuple.

    """
    layer = crs = dimValues = renderOpts = bbox = NotImplemented

    def getImage(self, bbox, width, height):
        """
        Create an image of a sub-bbox of a given size.

        @param bbox: A bbox tuple (llx, lly, urx, ury).  bbox will
            always lie within the self.layer.getBBox(self.crs)
        @param width: width in pixels.
        @param height: height in pixels.
        :return: A PIL Image object.

        """
        raise NotImplementedError

