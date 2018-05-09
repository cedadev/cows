# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

# Adapted for numpy/ma/cdms2 by convertcdms.py
"""
Implementation of station point rendering classe.

@author: Arif Shaon
"""

import os
import sys
import ImageColor, Image, ImageDraw, ImageFont
from cows.service.imps.StationCollection import StationCollection
from cows.bbox_util import geoToPixel

import pylons

import logging
log = logging.getLogger(__name__)

class PointRenderer():


    mimeType = 'image/png'

    def renderPoint(self, bbox, stations, width, height, cmap, icon ):
        """Creates an RGBA PNG with each station within given BBox represented by an icon.
        """

        # calculate BBox area
        bboxW = bbox[2] - bbox[0]
        bboxH = bbox[3] - bbox[1]
        bboxA = bboxW * bboxH
        log.debug("bbox area %s" % bboxA)

        #load the primary icon using the icon path
        point = Image.open(icon)

        # create a transparent background image
        tileImg = Image.new('RGBA', (width, height), (0,0,0,0))

        #go through each station in the station list paste its location on to the tileimg

        for station in stations:
                # if station contains data between 2006-1-1 and 2006-12-31 (
                # csmlGrapher is designed to handle datasets between these dates)
                if station.checkDates("2006-01-01","2006-12-31"):
                        # then load a different icon to identify that, else keep the original icon
                        point = Image.open(icon+'1')
                else:
                        point = Image.open(icon)
                # convert lon, lat to x, y coordiate of the image
                ox,oy = geoToPixel(station.lon, station.lat, bbox, width, height)
                # if bbox area is less than 100 then print name of each station next to its icon
                if bboxA < 100:
                        tileImg.paste(self.txt2img(station.desc, "lubR08.pil"),(ox+16, oy+5) )

                
                tileImg.paste(point, (ox-10, oy-9))

        return tileImg


    def txt2img(self, label, fontname="courB08.pil", imgformat="PNG", fgcolor=(0,0,0), bgcolor=(255,255,255),rotate_angle=0):

        """Render text as image."""
        fontpath = pylons.config['pilfonts_dir']
        font = ImageFont.load(os.path.join(fontpath,fontname))
        imgOut = Image.new("RGBA", (20,49), (0,0,0,0))

        # calculate space needed to render text
        draw = ImageDraw.Draw(imgOut)
        sizex, sizey = draw.textsize(label, font=font)

        imgOut = imgOut.resize((sizex,sizey))

        # render text into image draw area
        draw = ImageDraw.Draw(imgOut)
        draw.text((0, 0), label, fill=fgcolor, font=font)

        if rotate_angle:
                imgOut = imgOut.rotate(rotate_angle)

        return imgOut
