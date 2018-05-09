# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
An implementation of model.WebMapService driven from a CSML file.

@author: Stephen Pascoe
"""

from model import WebMapService, Layer, Dimension
import cdms, csml
from wms_cdms import SimpleCdmsLayer, CdmsGrid
import tempfile, os, sys


class CsmlDataset(object):
    """Abstract class defining how CsmlLayer objects can expect to extract data from the CSML.
    """

    def selectFeature(self, featureId, bbox, dimensionSpec):
        """
        @param featureId: The id of the feature within the dataset.
        @param bbox: The bounding box to extract.
        @param dimensionSpec: A dictionary of dimension values.
        @return: A CDMS variable of the extracted data.
        """
        raise NotImplementedError


class CachedCsmlDataset(CsmlDataset):
    """Maintains a cache of NetCDF data extracted from CSML.
    """

    def __init__(self, csmlDataset, tempdir=None):
        self.dataset = csmlDataset
        if tempdir:
            self._tempdir = tempfile.mkdtemp('', 'pywms', tempdir)
        else:
            self._tempdir = tempfile.mkdtemp('', 'pywms')
        self._map = {}

    def __del__(self):
        """
        Delete contents of self._tempdir
        """
        for f in self._map.values():
            os.remove(f)
        os.rmdir(self._tempdir)

    def selectFeature(self, featureId, bbox, dimensionSpec):
        cacheKey = (featureId, self._makeDimKey(dimensionSpec))
        try:
            ncfilename = self._map[cacheKey]
        except KeyError:
            (fd, ncfilename) = tempfile.mkstemp('.nc', featureId+'_', self._tempdir)
            os.close(fd)
            feature = self.dataset.getFeature(featureId)
            self._extract(feature, dimensionSpec, ncfilename)
            #self._map[cacheKey] = ncfilename

        d = cdms.open(ncfilename)
        (lon1, lat1, lon2, lat2) = bbox
        var = d(featureId, latitude=(lat1, lat2), longitude=(lon1, lon2), squeeze=1)
        d.close()

        return var

    def _extract(self, feature, dimensionSpec, ncfilename):
        feature.subsetToGridSeries(ncpath=ncfilename, **dimensionSpec)
        
    def _makeDimKey(self, dimensionSpec):
        i = dimensionSpec.items(); i.sort()
        return tuple(i)

class CsmlLayer(Layer):
    """
    This layer extracts selected grids to a temporary NetCDF file and then uses CDMS
    to serve the data.
    """

    def __init__(self, csmlFeatureId, csmlDataset, minValue, maxValue):
        """
        @param csmlFeatureId: The id of the feature instance.
        @param csmlDataset: A CsmlDataset instance.

        @todo: Get units
        @todo: tidy up where features are referenced.
        """

        feature = csmlDataset.dataset.getFeature(csmlFeatureId)
        try:
            long_name = feature.description.CONTENT
        except AttributeError:
            long_name = id

        super(CsmlLayer, self).__init__(long_name)

        self.dimensions = dict(time=CsmlTimeDimension(feature.getDomain()['time']))
        self.minValue = minValue
        self.maxValue = maxValue
        self.units = '!TODO: Get units from CSML'

        self.featureId = csmlFeatureId
        self.dataset = csmlDataset

    def selectGrid(self, bbox, dimensionSpec):
        """It is probably better to extract the entire grid for a time point and cache it.
        """
        (lon1, lat1, lon2, lat2) = bbox

        # Hack to get around CSML not understanding <time>Z
        #!TODO: find a better solution or get it implemented in CSML.
        if 'time' in dimensionSpec:
            if dimensionSpec['time'][-1] == 'Z':
                dimensionSpec['time'] = dimensionSpec['time'][:-1]
        
        var = self.dataset.selectFeature(self.featureId, bbox, dimensionSpec)
        return CdmsGrid(var)


class CsmlTimeDimension(Dimension):
    def __init__(self, extent):
        self._extentList = extent
        self.units = 'ISO 8601'

    def _getExtent(self):
        return ','.join('%sZ' % x for x in self._extentList)
    extent = property(_getExtent)

class CsmlWMS(WebMapService):
    """
    """
    
    def __init__(self, title, csmlFilename, layerPrefs={}, exclude=[], tempdir=None):
        super(CsmlWMS, self).__init__(title)

        self._dataset = csml.parser.Dataset()
        self._dataset.parse(csmlFilename)
        self._cache = CachedCsmlDataset(self._dataset, tempdir)

        for field in self._dataset.getFeatureList():
            if field in exclude:
                continue

            if field in layerPrefs:
                minValue = layerPrefs[field].get('minValue')
                maxValue = layerPrefs[field].get('maxValue')
            else:
                minValue = None
                maxValue = None
            
            self.layers[field] = CsmlLayer(field, self._cache, minValue, maxValue)
