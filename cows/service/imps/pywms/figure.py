# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Publication quality plotting engine.

:author: Stephen Pascoe
"""

import os
from tempfile import mkstemp
from cStringIO import StringIO

from matplotlib.toolkits.basemap import Basemap
import pylab as p
from matplotlib import cm
try: 
    from PIL import Image
except ImportError:
    import Image
import Numeric as N
import MA

from pywms.utils import word_wrap

class Figure(object):
    """Render a grid to a publication-quality figure.

    :cvar supportedFormats: A list of supported mime-types

    :ivar grid: The grid to render
    :ivar cmap: The colourmap to use for type 'colour'
    :ivar caption: A caption under the figure
    :ivar type: 'colour' or 'contour'
    :ivar format: The mime-type to use when rendering
    """

    supportedFormats = ['image/png', 'image/jpeg', 'application/postscript', 'image/svg+xml']

    def __init__(self, grid=None, cmap=cm.get_cmap, caption='', type='colour', format='image/png',
                 vmin=None, vmax=None):
        self.grid = grid
        self.cmap = cmap
        self.cmap.set_bad('#000000', alpha=0.0)
        self.caption = caption
        self.type = type
        self.format = format
        self.vmin=vmin
        self.vmax=vmax



    def makeFigure(self):
        """
        :todo: Uses pylab so may not be threadsafe.
        """

        lon = self.grid.lon0 + N.arrayrange(self.grid.nlon)*self.grid.dlon
        lat = self.grid.lat0 + N.arrayrange(self.grid.nlat)*self.grid.dlat

        ll_lon, ll_lat = lon[0], lat[0]
        ur_lon, ur_lat = lon[-1], lat[-1]

        # Account for variable lat/lon axis ordering
        #!TODO: Could we move this (along with the equivilent in render_imp.py into grid.py?
        if self.grid.ilat < self.grid.ilon:
            latLonOrdering = True
        else:
            latLonOrdering = False

        if latLonOrdering:
            var = self.grid.value
        else:
            var = MA.transpose(self.grid.value)
            

        fig = p.figure()
        map = Basemap(projection='cyl', llcrnrlon=ll_lon, llcrnrlat=ll_lat,
                      urcrnrlon=ur_lon, urcrnrlat=ur_lat, resolution='l')

##         if self.grid.units:
##             p.title("%s\n(%s)" % (self.grid.long_name, self.grid.units))
##         else:
##             p.title(self.grid.long_name)
        p.title(self.grid.long_name)

        if self.type == 'colour':
            # transform_scalar doesn't support masked arrays so we must fill then replace the mask.
            var_dat = map.transform_scalar(var.filled(1.0e20), lon,
                                           lat, len(lon), len(lat))
            var = MA.masked_values(var_dat, 1.0e20)
            map.imshow(var, cmap=self.cmap, vmin=self.vmin, vmax=self.vmax,
                       interpolation='nearest')
            cbar = p.colorbar(orientation='horizontal', format='%.2g')
            if self.grid.units:
                cbar.ax.set_xlabel(self.grid.units)
            
        else:
            x, y = map(*p.meshgrid(lon, lat))
            c = map.contour(x, y, var, 12, colors='black')
            c.clabel(fontsize=8)
            map.fillcontinents(color='#e0e0e0')

        map.drawcoastlines(color='gray')

        map.drawmeridians(p.arange(-180,180,30), labels=[1,0,0,1], color='gray')
        map.drawparallels(p.arange(-90,90,15), labels=[1,0,0,1], color='gray')

        # Wrap the caption
        caption = word_wrap(self.caption, 80)

        fig.text(0.1, 0.08, caption,
                 fontsize=10, horizontalalignment='left',
                 verticalalignment='top',
                 transform=fig.transFigure
                 )

        return fig

    def render(self, fh):
        """Render the figure and serialise it to a file stream.

        @param fh: A file object
        """
        
        fig = self.makeFigure()
        
        ext = self.getExtension()

        # matplotlib can't write jpeg on my installation
        if ext == '.jpg':
            convertTo = 'JPEG'
            ext = '.png'
        else:
            convertTo = None

        (fh1, fn) = mkstemp(ext, 'pywms_tmp_')
        os.close(fh1)
        fig.savefig(fn)

        if convertTo:
            img = Image.open(fn)
            buf = StringIO()
            img.save(buf, convertTo)
            fh.write(buf.getvalue())
        else:
            fh.write(open(fn).read())

        os.remove(fn)

    def getExtension(self):
        (mt, smt) = self.format.split('/')
        if smt == 'png':
            ext = '.png'
        elif smt == 'jpeg':
            ext = '.jpg'
        elif smt == 'postscript':
            ext = '.eps'
        elif smt == 'svg+xml':
            ext = '.svg'

        return ext

def makeTimeSeriesFigure(ts):
    """
    :todo: time axis labelling
    :todo: Flesh out TimeSeries interface so that this function doesn't need to use cdms calls.
    """
    p.figure()
    p.title(ts.long_name)
    try:
        p.ylabel(ts.units)
    except AttributeError:
        pass

    p.plot(ts.value.getTime().getValue(), ts.value.filled(0.0), '-o')
    (fh, fn) = mkstemp('.png', 'pywms_tmp_')
    os.close(fh)
    p.savefig(fn)
    img = Image.open(fn); img.load()
    os.remove(fn)

    return img
