# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
A place to put configuration settings for the csmlbackend package.

csmlbackend shouldn't directly reference pylons.config so set options in here.

Any values starting with cows.csml in the plylons config file will overwrite 
these values, see cows.pylons.config.py for details.
"""

config = dict(
    # Directory where GridSeries are temporarily extracted to.
    tmpdir = '/tmp',
    # Name of the matplotlib colourmap to use
    colourmap = 'jet',
    # Where to publish CSML documents to
    publish_dir = '/tmp',
    # Where CSML sources are stored
    csmlstore = None,
    # Where the ndg configuration is, if required
    ndgconfig = None,
    # Location of WFS config file
    wfsconfig = None,
    # Location of legend font
    legendfont = '/usr/share/fonts/truetype/msttcorefonts/arial.ttf',
    )
