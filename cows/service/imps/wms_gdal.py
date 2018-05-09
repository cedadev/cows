# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
An implementation of cows.service.wms_iface that uses GDAL to support
warping between multiple coordinate reference systems.  This implementation
relies on a further interface, IGDALDataSource, to provide the data.

:todo: The source is a little confused about the difference between
    Dataset (i.e. a GDAL Dataset object) and DataSource (A wrapper
    around a GDAL dataset defined in IGDALDataSource).  Fix this.

"""
from cows.service.wxs_iface import ILayerMapper
from cows.service.wms_iface import IwmsLayer, IwmsDimension, IwmsLayerSlab
from cows.bbox_util import geoToPixel
from osgeo import osr, gdal

try: 
    from PIL import Image
except ImportError:
    import Image

import logging
log = logging.getLogger(__name__)

class IGDALDataSource(object):
    """
    This interface is very similar to ILayer except that it returns GDAL
    datasets rather than PIL images.  It also doesn't try to handle multiple
    CRSs as this is handled by GDALLayer.  

    :ivar title: The layer title.  As seen in the Capabilities document.
    :ivar abstract:  Abstract as seen in the Capabilities document.
    :ivar dimensions: A mapping of dimension names to IDimension objects.
    :ivar units: A string describing the units.
    :ivar crs: The CRS that GDAL datasets will be returned in by
        self.getDataset()

    :todo: Legend plotting needs support but should probably be done in a
        seperate interface.

    """
    dimensions = NotImplemented

    def getWKT(self):
        """
        Because mapping between CRS codes and WKT format can be flaky in GDAL
        this function allows the problem to be solved on a case-by-case basis.
        
        :return: the description of self.crs in GDAL well known text format.

        """
        
    def getBBox(self):
        """
        :return: the bounding box (llx, lly, urx, ury) in self.crs.

        """

    def getDataset(self, dimValues=None, renderOpts={}):
        """
        Create the equivilent of ILayerSlab as a GDAL dataset.  The dataset
        could have 1,3 or 4 bands representing PIL modes 'L', 'RGB' or 'RGBA'.
        
        @param dimValues: A mapping of dimension names to dimension values
            as specified in the IDimension.extent.
        @param renderOpts: A generic mapping object for passing rendering
            options.
        :return: A GDAL Dataset object for this horizontal slice.
            
        """


class GDALLayer(IwmsLayer):
    """
    This implementation of IwmsLayer can warp images from a source CRS to
    various other CRSs.

    :ivar sourceCRS: The CRS of the data source.
    :ivar warpCRS: A mapping of CRS identifiers to WKT descriptions of
       CRSs that are supported for this ILayer via warping.

    """

    def __init__(self, dataSource):
        """
        @param dataSource: A IGDALDataSource implementation.

        """
        self._ds = dataSource
        self.warpCRS = {}
        self.sourceCRS = dataSource.crs

        self.title = dataSource.title
        self.abstract = dataSource.abstract
        self.dimensions = dataSource.dimensions
        self.units = dataSource.units
        #!NOTE: self.crss is implemented as property

    def _getCRSs(self):
        return [self._ds.crs] + self.warpCRS.keys()
    crss = property(_getCRSs)

    def getBBox(self, crs):
        src_bb = self._ds.getBBox()
        if crs == self.sourceCRS:
            return src_bb

        sr_src = osr.SpatialReference(self._ds.getWKT())
        sr_dst = osr.SpatialReference(self.warpCRS[crs])

        ct = osr.CoordinateTransformation(sr_src, sr_dst)

        llx, lly = ct.TransformPoint(float(src_bb[0]), float(src_bb[1]))[:2]
        urx, ury = ct.TransformPoint(float(src_bb[2]), float(src_bb[3]))[:2]
        return (llx, lly, urx, ury)

    def getSlab(self, crs, dimValues=None, renderOpts={}):
        return GDALLayerSlab(self, crs, dimValues=dimValues,
                             renderOpts=renderOpts)

    def getCacheKey(self, crs, dimValues=None, renderOpts={}):
        """
        A fairly sane cache key generation algorithm.

        """
        if dimValues is None:
            x = None
        else:
            x = dimValues.items()
        x.sort()
        y = renderOpts.items(); y.sort()

        return str((x, y))

class GDALLayerSlab(IwmsLayerSlab):
    def __init__(self, layer, crs, dimValues=None, renderOpts={}):
        self.layer = layer
        self.crs = crs
        self.dimValues = dimValues
        self.rendOpts = renderOpts
        self.bbox = layer.getBBox(crs)
        
        if crs == layer.sourceCRS:
            self._data = layer._ds.getDataset()
        else:
            self._data = warpDataset(layer._ds, layer.warpCRS[crs])

    def getImage(self, bbox, width, height):        
        # Calculate the pixel coordinates of bbox within self.bbox
        w, h = self._data.RasterXSize, self._data.RasterYSize
        llx, lly = geoToPixel(bbox[0], bbox[1], self.bbox, w, h)
        urx, ury = geoToPixel(bbox[2], bbox[3], self.bbox, w, h)
        xoff, yoff = llx, ury
        xsize, ysize = urx-llx, lly-ury

        img = datasetToImage(self._data, xoff, yoff, xsize, ysize)
        return img.resize((width, height))

#-----------------------------------------------------------------------------
# Utility functions

def datasetToImage(ds, xoff, yoff, xsize, ysize):
    """
    Convert a GDAL dataset into a PIL image with cropping.

    """
    bandImages = []
    for iband in range(1, ds.RasterCount+1):
        band = ds.GetRasterBand(iband)
        bandImages.append(Image.fromstring('L', (xsize, ysize),
                                           band.ReadRaster(xoff, yoff,
                                                           xsize, ysize)))
    return Image.merge('RGBA', bandImages)

def warpDataset(dataSource, wkt, driverName='MEM', datasetName=''):
    """
    Warp a GDAL dataset from one CRS to another.

    @param dataset: An object implementing IGDALDataSource.
    @param wkt: The Well Known Text string of the destination CRS
    @param driverName: The GDAL driver to use for the new dataset.
        This driver must support the Create() method.
    @param datasetName: The name to give the dataset (i.e. the filename if
        a file-based driver)
    @param return: A GDAL dataset in the new CRS.

    """
    ds = dataSource.getDataset()

    sr_src = osr.SpatialReference(dataSource.GetProjection())
    sr_dst = osr.SpatialReference(wkt)
    ct = osr.CoordinateTransform(sr_src, sr_dst)

    # What is a reasonable resolution?  We should transform the resolution
    # of the source image into the new coordinates
    T = ds.GetGeoTransform()
    #!TODO ...
    

    dr = gdal.GetDriverByName(driverName)
    #!TODO: How big should the image be? Just fudge the issue for now.
    dsOut = dr.Create(datasetName, width, height, 4,
                      gdal.GDT_Byte)
    dsOut.SetProjection(wkt)

    # We need to calculate the warped GeoTransform
    topLeft = ct(T[0], T[3])


    gdal.ReprojectImage(ds, dsOut, ds.GetProjection(), wkt)
    return dsOut
    


