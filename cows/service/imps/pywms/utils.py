# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
General utilitiy function

@author: Stephen Pascoe
"""

from ogc_exceptions import ServiceException

def retrieveOWSParams(paramDict, keys):
    """Retrieve parameters from a wsgi_request object raising
    ServiceException where appropriate.

    @param paramDict: Dictionary of parameters
    @param keys: The parameter names to extract
    @return: A dictionary of retrieved parameters.
    """

    ret = {}
    for param in keys:
        try:
            val = paramDict[param]
        except KeyError:
            raise ServiceException("Parameter %s not specified" % param)

        ret[param] = val

    return ret

def parseBBOX(bboxStr):
    """Parse a bbox string and return a tuple of floats.
    """

    try:
        bbox = [float(x) for x in bboxStr.split(',')]
        x1,y1,x2,y2 = bbox
    except ValueError:
        raise ServiceException("Incorrect BBOX specification %s" % bboxStr)

    # Openlayers can ask for some odd BBOXs.  Try truncating
    #x1 = max(-180., min(180., x1))
    #x2 = max(-180., min(180., x2))
    #y1 = max(-90., min(90., y1))
    #y2 = max(-90., min(90., y2))

    print '== %s,%s,%s,%s' % (x1,y1,x2,y2)
    
    # Enforce strict CRS:84 BBOX
    try:
        assert x1 >= -180 and x1 <= 180
        assert x2 >= -180 and x2 <= 180
        assert y1 >= -90 and y1 <= 90
        assert y2 >= -90 and y2 <= 90
        assert x1 < x2
        assert y1 < y2
    except AssertionError:
        raise ServiceException("Incorrect BBOX specification %s" % bboxStr)
        
    return (x1,y1,x2,y2)


class BBox(object):
    """Class to encapsulate a WMS BBOX and do some basic arrithmatic.

    Openlayers will ask for BBOXs out of the CRS:84 bounds.  Methods in this
    class help handle this.
    """

    def __init__(self, bbox):
        # sanity check
        (x1,y1,x2,y2) = bbox

        self.bbox = bbox

    def _getCRS84(self):
        """
        @return: the BBOX tuple truncated to CRS:84
        """

        (x1,y1,x2,y2) = self.bbox
         
        x1 = max(-180., min(180., x1))
        x2 = max(-180., min(180., x2))
        y1 = max(-90., min(90., y1))
        y2 = max(-90., min(90., y2))

        return (x1,y1,x2,y2)
    crs84 = property(_getCRS84)

    def getOffset(self):
        """
        @return: the offset of the bottom left coordinate of the CRS:84 bounding box from the raw bbox
        """
        (x1,y1,x2,y2) = self.bbox
        (x3,y3,x4,y4) = self.crs84

        return (x3-x1, y3-y1)
        
    def getCrs84OffsetInImage(self, width, height):
        """
        @param width: width of image in pixels
        @param height: height of image in pixels
        @return: the (x,y) offset of the CRS:84 bbox in the full bbox for an image of given dimensions.
            Note this the offset from the top-left of the image.
        """
        (x1,y1,x2,y2) = self.bbox
        (x3,y3,x4,y4) = self.crs84
        bwidth = x2 - x1
        bheight = y2 - y1

        # The upper left corner relative to full bbox
        ulx, uly = x3-x1, y2-y4

        # Scale to image size
        return (int(round(ulx / bwidth * width)), int(round(uly / bheight * height)))

    def getCrs84ImageSize(self, width, height):
        """
        @param width: width of the image covering the full bbox
        @param height: height of the image covering the full bbox
        @return: (width, height) in pixels
        """
        (x1,y1,x2,y2) = self.bbox
        (x3,y3,x4,y4) = self.crs84

        xscale = width / (x2 - x1)
        yscale = height / (y2 - y1)

        return (int(round((x4-x3) * xscale)), int(round((y4-y3) * yscale)))

    def _getCrs84Width(self):
        (x1,y1,x2,y2) = self.crs84
        return x2-x1
    crs84Width = property(_getCrs84Width)

    def _getCrs84Height(self):
        (x1,y1,x2,y2) = self.crs84
        return y2-y1
    crs84Height = property(_getCrs84Height)


def reconstructURL(environ, withQueryString=True):
    """
    Code from WSGI PEP with slight modifications.
    """

    from urllib import quote
    from urlparse import urlparse

    url = environ['wsgi.url_scheme']+'://'

    isForwarded = False
    # If request being proxied
    if 'HTTP_X_FORWARDED_HOST' in environ:
        isForwarded = True
    elif 'HTTP_HOST' in environ:
        url += environ['HTTP_HOST']
    else:
        url += environ['SERVER_NAME']

    if isForwarded:
        # Get URL from referer
        # proxy path can be configured separately for when HTTP_REFERER
        # isn't exposed.
        try:
            url = environ['paste.config']['proxy_path']
        except KeyError:
            url = environ['HTTP_REFERER']
    else:
        # Sometimes HTTP_HOST will already have the port
        url_bits = urlparse(url)
        if ':' not in url_bits[1]:
            if isForwarded:
                if 'HTTP_X_FORWARDED_PORT' in environ:
                    url += ':' + environ['HTTP_X_FORWARDED_PORT']
            elif environ['wsgi.url_scheme'] == 'https':
                if environ['SERVER_PORT'] != '443':
                   url += ':' + environ['SERVER_PORT']
            else:
                if environ['SERVER_PORT'] != '80':
                   url += ':' + environ['SERVER_PORT']

    url += quote(environ.get('SCRIPT_NAME',''))
    url += quote(environ.get('PATH_INFO',''))
    if withQueryString and environ.get('QUERY_STRING'):
        url += '?' + environ['QUERY_STRING']

    return url


def word_wrap(text, width):
    """
    A word-wrap function that preserves existing line breaks
    and most spaces in the text. Expects that existing line
    breaks are posix newlines (\n).

    @note: From ASPN online Python cookbook.  Adapted to break on \\n.
    @author: Mike Brown
    """
    return reduce(lambda line, word, width=width: '%s%s%s' %
                  (line,
                   ' \n'[(len(line)-line.rfind('\n')-1
                         + len(word.split('\n',1)[0]
                              ) >= width)],
                   word),
                  text.split('\n')
                 )
