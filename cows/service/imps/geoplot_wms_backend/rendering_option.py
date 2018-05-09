# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

'''
Created on 7 Sep 2009

@author: pnorton
'''

class RenderingOption(object):
    '''
    classdocs
    '''


    def __init__(self, name, title, type, default, options=None):
        '''
        Constructor
        '''
        
        self.name = name
        self.title = title
        self.type = type
        self.default = default
        self.options = options