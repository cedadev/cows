# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Implements the WMS interfaces for simple CDMS variables

This implementation is for backward compatibility between the old interface and
the new.  Only one CRS per layer is supported.

"""
from ows_common.service.wms_iface import ILayer, ILayerSlab, IDimension
from wms_cdms import SimpleCdmsLayer, CdmsTimeDimension, CdmsGrid
import cdtime
from render_imp import RGBARenderer
from matplotlib.cm import get_cmap
from matplotlib.colorbar import ColorbarBase
from matplotlib.ticker import LinearLocator
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from numpy import arange

from cStringIO import StringIO
try: 
    from PIL import Image
except ImportError:
    import Image

import logging
log = logging.getLogger(__name__)

class CdmsLayer(ILayer):
    """
    The ILayer interface has superceded model.Layer and therefore CdmsLayer
    does not inherit from model.Layer or SimpleCdmsLayer.  Instead encapsulation
    is used.

    """

    featureInfoFormats = ['text/html']
    
    def __init__(self, cdmsVar, GridClass=CdmsGrid, minValue=None, maxValue=None,
                 units=None):
        try:
            self.title = cdmsVar.long_name
        except AttributeError:
            self.title = cdmsVar.id

        self._layer = SimpleCdmsLayer(cdmsVar, GridClass=GridClass)
        self.abstract = None
        self.crss = [GridClass.crs]
        #!TODO: do this properly
        self.wgs84BBox = (-15.0, 45.0, 15.0, 60.0)
        if units:
            self.units = units
        else:
            self.units = self._layer.units
        self.minValue = minValue
        self.maxValue = maxValue

        self.legendSize=(100, 500)

        dims = {}
        for dimName, dim in self._layer.dimensions.items():
            dims[dimName] = Dimension(dim)
        self.dimensions = dims

    def getBBox(self, crs):
        # Get BBOX from pywms layer
        var = self._layer.var
        xAxis = var.getAxis(var.getAxisIndex('eastings'))
        yAxis = var.getAxis(var.getAxisIndex('northings'))
        #!NOTE order specific code
        return (xAxis[0], yAxis[-1], xAxis[-1], yAxis[0])

    def getSlab(self, crs, dimValues=None, renderOpts={}):
        if crs != self.crss[0]:
            raise ValueError("CRS %s not supported on this layer" % crs)
        
        return CdmsLayerSlab(crs, dimValues, renderOpts, self)

    def getCacheKey(self, crs, dimValues=None, renderOpts={}):
        # Don't support caching
        return None

    def getLegendImage(self, orientation='vertical', renderOpts={}):
        if 'vert' in orientation:
            figsize = (1, 5)
            rect = (0.05, 0.05, 0.4, 0.9)
        else:
            figsize = (5, 1)
            rect = (0.05, 0.55, 0.9, 0.4)
            
        
        fig = Figure(figsize=figsize, dpi=100)
        ax = fig.add_axes(rect)
        boundaries = arange(self.minValue, self.maxValue,
                           float(self.maxValue-self.minValue)/256)
        loc = LinearLocator()
        loc.set_bounds(self.minValue, self.maxValue)
        ColorbarBase(ax, boundaries=boundaries, orientation=orientation, ticks=loc(),
                     cmap=get_cmap(renderOpts.get('cmap', 'Paired')))

        if 'vert' in orientation:
            ax.set_ylabel(self.units)
        else:
            ax.set_xlabel(self.units)

        c = FigureCanvas(fig)
        c.draw()
        buf = StringIO()
        c.print_png(buf)
        buf.seek(0)
        img = Image.open(buf)

        return img

    def getFeatureInfo(self, format, crs, point, dimValues):
        # We assume here format and crs are valid (the framework should check).
        (x, y) = point

        var = self._layer.var
        # Get the data at that point
        sel = dict(eastings=x, northings=y)
        # Ignore dimvalues
        # sel.update(dimValues)
        val = var(**sel)
        
        return '''
<html>
<body>
<h1>GetFeatureInfoResponse for layer: %s</h1>
Selection: %s<br/>
Value: %s<br/>
</body>
</html>
''' % (self.title, sel, val)
        

class CdmsLayerSlab(ILayerSlab):
    def __init__(self, crs, dimValues, renderOpts, layer):
        self.crs = crs
        self.dimValues = dimValues
        self.renderOpts = renderOpts
        self.layer = layer
        self.bbox = layer.getBBox(crs)

        self._renderer = RGBARenderer(self.layer.minValue, self.layer.maxValue)

    def getImage(self, bbox, width, height):
        grid = self.layer._layer.selectGrid(bbox, self.dimValues)
        cmap = get_cmap(self.renderOpts.get('cmap', 'Paired'))
        img = self._renderer.renderGrid(grid, bbox, width, height, cmap)

        return img

    def getCacheKey(self):
        raise NotImplementedError
    

class Dimension(IDimension):
    """
    Wrapper to fix some interface differences.

    """
    def __init__(self, pywmsDim):
        self.units = pywmsDim.units
        self.extent = pywmsDim.extent.split(',')
