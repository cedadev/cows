# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
An implementation of model.WebMapService drived from a single CDMS
file, potentially a CDML aggregation file.
"""

from model import Layer, Grid
import cdtime, cdutil, re
import cdms2 as cdms
from ows_common.exceptions import InvalidParameterValue
import numpy.oldnumeric.ma as MA
import numpy.oldnumeric as N

class GridError(Exception):
    pass

class CdmsGrid(Grid):
    """An adaptor for a cdms variable.
    """

    def __init__(self, var, title=None):
        """
        @param var: The cdms variable.  This should be of shape (x, lat).
        """

        try:
            self._var = var
            self._setGrid()
        except GridError, e:
            # This isn't a simple grid
            #!TODO: we could regrid here.
            raise e
        self._setMetadata(title=title)


    def _setGrid(self):
        """Check the grid is simple and initialise.
        """

        y = self.getYAxis()
        dy_a = y[1:] - y[:-1]
        if not (dy_a == (N.ones(len(dy_a)) * dy_a[0])).all():
            raise SimpleGridError, "Y Axis not equally spaced"
        self.y0 = y[0]
        self.dy = dy_a[0]
        self.ny = len(y)
        self.iy = self._var.getAxisList().index(y)

        x = self.getXAxis()
        dx_a = x[1:] - x[:-1]
        if not (dx_a == (N.ones(len(dx_a)) * dx_a[0])).all():
            raise SimpleGridError, "X Axis not equally spaced"
        self.x0 = x[0]
        self.dx = dx_a[0]
        self.nx = len(x)
        self.ix = self._var.getAxisList().index(x)


    def _setMetadata(self, title=None):
        if title:
            self.long_name = title
        else:
            try:
                self.long_name = self._var.long_name
            except AttributeError:
                self.long_name = 'Unknown'

        try:
            self.units = self._var.units
        except AttributeError:
            self.units = ''

    def _getValue(self):
        return self._var
    value = property(_getValue)


class CdmsLatLonGrid(CdmsGrid):
    """
    Specialise CdmsGrid for EPSG:4326

    """

    crs = 'EPSG:4326'

    def getXAxis(self):
        return self._var.getLongitude()
    def getYAxis(self):
        return self._var.getLatitude()

class CdmsBNGGrid(CdmsGrid):
    """
    Specialise CdmsGrid for British National Grid coordinate system

    EPSG:27700 OSGB:36

    """

    crs = 'EPSG:27700'
    
    def getXAxis(self):
        return self._var.getAxisList()[1]
    def getYAxis(self):
        return self._var.getAxisList()[0]



class SimpleCdmsLayer(Layer):
    def __init__(self, cdmsVar, minValue=None, maxValue=None, GridClass=CdmsGrid):
        """
        @param cdmsVar: variable object

        @todo: Add crs attribute
        """

        self.GridClass = GridClass

        self.var = cdmsVar
        try:
            long_name = self.var.long_name
        except AttributeError:
            long_name = self.var.id

        super(SimpleCdmsLayer, self).__init__(long_name)

        #if 'time' in self.var.axes:
        #    self.dimensions = dict(time=CdmsTimeDimension(self.var.axes['time']))
        if self.var.getTime():
            self.dimensions = dict(time=CdmsTimeDimension(self.var.getTime()))
        else:
            self.dimensions = {}

##         if minValue is not None:
##             self.minValue = minValue
##         else:
##             self.minValue = self.var.min_value

##         if maxValue is not None:
##             self.maxValue = maxValue
##         else:
##             self.maxValue = self.var.max_value

        self.minValue = minValue
        self.maxValue = maxValue

        try:
            self.units = self.var.units
        except AttributeError:
            self.units = '?'

    def selectGrid(self, bbox, dimensionSpec):
        """
        @warning: Hacked for UKCIP02.
        @todo: replace lat/lon references with generic X/Y code.

        """
        (lon1, lat1, lon2, lat2) = bbox
        sel = dict(northings=(lat1, lat2, 'cce'), eastings=(lon1, lon2, 'cce'))
        if 'time' in self.dimensions:
            sel['time'] = self.dimensions['time'].iso2reltime(dimensionSpec['time'])
        sel['squeeze'] = 1
            
        v = self.var(**sel)
        return self.GridClass(v, title=self.title)

    def describe(self, dimensionSpec):
        return self.var.long_name + ' at ' + self.dimensions['time']



class CdmsTimeDimension(object):
    """
    @todo: Move to impl.py when interface migration complete.

    """
    def __init__(self, timeAxis):
        self._axis = timeAxis
        self.units = 'ISO8601'

    def _getExtent(self):
        comptimes = self._axis.asComponentTime()
        return ','.join(['%s-%s-%sT%s:%s:%sZ' % (x.year, x.month, x.day,
                                                 x.hour, x.minute, x.second)
                         for x in comptimes])
    extent = property(_getExtent)

    def iso2reltime(self, time, yearOverride=None):
        mo = re.match(r'(\d+)-(\d+)-(\d+)T(\d+):(\d+):([0-9.]+)Z', time)
        if not mo:
            raise InvalidParameterValue('Time %s not recognised' % time, 'time')
        (year, month, day, hour, minute, second) = mo.groups()
        if yearOverride:
            year = yearOverride
        c = cdtime.comptime(int(year), int(month), int(day),
                            int(hour), int(minute), float(second))
        return c.torel(self._axis.units)

    def iso2timeDelta(self, time):
        return [self.iso2reltime(x) for x in time.split('D')]





#-----------------------------------------------------------------------------

import unittest

class TestBNGGrid(unittest.TestCase):
    def setUp(self):
        import os

        try:
            self.data_dir = os.environ['TEST_DATA_DIR']
            self.rainfall = cdms.open(self.data_dir+'/ukcip02/rainfall_1961-2000.nc')
        except:
            raise RuntimeError("""
Test data not found.  Please set the TEST_DATA_DIR environment variable.
""")

        # wire in the render_imp logger to nose
        import render_imp
        render_imp.logger = render_imp.logging.getLogger('nose.render_imp')
  

    def _makeGrid(self):
        v = self.rainfall['rainfall'][0]
        self.assertEquals(v.id, 'rainfall')
        return CdmsBNGGrid(v, 'UKCIP02 rainfall data')

    def testGridAttributes(self):
        g = self._makeGrid()

        self.assertEquals(g.dx, 5000)
        assert g.dy == -5000
        self.assertEquals(g.nx, 180)
        assert g.ny == 290
        assert g.x0 == -200000
        assert g.y0 == -200000
        self.assertNotEquals(g.ix, g.iy)

    def testGridValue(self):
        g = self._makeGrid()
        v = g.value

        # Value should be masked
        assert v.mask()

    def testRender(self):
        from render_imp import RGBARenderer
        from matplotlib.cm import get_cmap

        g = self._makeGrid()
        # Set arbitary min/max values for now
        r = RGBARenderer(MA.minimum(g.value), MA.maximum(g.value))

        xn = g.x0+g.dx*g.nx
        yn = g.y0+g.dy*g.ny
        bbox = (min(g.x0, xn), min(g.y0, yn),
                max(g.x0, xn), max(g.y0, yn))

        img = r.renderGrid(g, bbox, 400, 400, get_cmap())
        img.save('whole_domain.png')

        assert img.size == (400, 400)

        bbox2 = (bbox[0], bbox[1], bbox[0] + (bbox[2]-bbox[0])/2,
                 bbox[1] + (bbox[3]-bbox[1])/2)
        img = r.renderGrid(g, bbox2, 400, 400, get_cmap())
        img.save('ll_quad.png')

        
