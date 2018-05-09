# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Utilities for manipulating bounding boxes as a tuple (llx, lly, urx, ury)

:note: This has no connection with the cows data model.  This module
    will probably move eventually.
    
"""

import math

def intersection(bbox1, bbox2):
    """
    Return a bbox of the intersection of bbox1 and bbox2.

    """
    llx = max(bbox1[0], bbox2[0])
    lly = max(bbox1[1], bbox2[1])
    urx = min(bbox1[2], bbox2[2])
    ury = min(bbox1[3], bbox2[3])

    return llx, lly, urx, ury

def union(bbox1, bbox2):
    """
    :ivar bbox1: bounding box tuple (llx, lly, urx, ury).
    :ivar bbox2: bounding box tuple (llx, lly, urx, ury) to aggregate with bbox1 
    :return: union of bbox1 and bbox2 as tuple, (llx, lly, urx, ury)
    """
    llx = min(bbox1[0], bbox2[0])
    lly = min(bbox1[1], bbox2[1])
    urx = max(bbox1[2], bbox2[2])
    ury = max(bbox1[3], bbox2[3])
    return llx, lly, urx, ury    

def relativeSize(bbox1, bbox2):
    """
    Calculate the relative size of bbox1 to bbox2.

    :return: (sx, sy) where bbox1_width = sx * bbox2_width, etc.

    """
    sx = (bbox1[2]-bbox1[0]) / (bbox2[2]-bbox2[0])
    sy = (bbox1[3]-bbox1[1]) / (bbox2[3]-bbox2[1])

    return (sx, sy)

def geoToPixel(x_g, y_g, bbox, width, height, roundUpX=False, roundUpY=False):
    """
    Calculate the pixel coordinate of a point within a bbox given the
    width and height of the bbox in pixels.

    This algorithm takes the origin of the bbox as the bottom left and
    the origin of the image as top left.

    @param x_g: x coordinate in goegraphic coordinates
    @param y_g: y coordinate in geographic coordinates
    @param bbox: The bounding box of the image
    @param width: The width of the image in pixels
    @param height: The height of the image in pixels.
    @param roundUpX: Round the X pixel value upwards.
    @param roundUpY: Round the y pixel value upwards.
    
    :return: (x,y) in pixel coordinates

    """

    x = (x_g - bbox[0])*width / (bbox[2]-bbox[0])
    y = (bbox[3] - y_g)*height / (bbox[3]-bbox[1])

    if roundUpX:
        x = math.ceil(x)
    if roundUpY:
        y = math.ceil(y)

    return int(x), int(y)

def pixelToGeo(x, y, bbox, width, height):
    """
    Calculate the geographic coordinates of a pixel on an image
    of given bbox and size.

    This algorithm takes the origin of the bbox as the bottom left and
    the origin of the image as top left.

    @param x: x coordinate in pixel coordinates
    @param y: y coordinate in pixel coordinates
    @param bbox: The bounding box of the image
    @param width: The width of the image in pixels
    @param height: The height of the image in pixels.
    
    :return: (x_g, y_g) in geographic coordinates
    
    """

    x_g = bbox[0] + ((bbox[2]-bbox[0]) / width)*x    
    y_g = bbox[3] - ((bbox[3]-bbox[1]) / height)*y

    return (x_g, y_g)
