# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

'''
Created on 9 Sep 2009

@author: pnorton

Fix to import the Image module whether it resided in PIL or not.
'''

try:
    from PIL import Image
except:
    import Image