# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import logging
import urllib2

from matplotlib import cm
from cows.service.imps.csmlbackend.config import config

log = logging.getLogger(__name__)

class SlabOptionsParser(object):
    
    def __init__(self, slabOptions, renderOptions):
        
        self._slabOptionsLookup = {}
        for option in slabOptions:
            self._slabOptionsLookup[option.name.lower()] = option
        
        
        
        self._renderOptions = {}
        for k, v in renderOptions.items():
            self._renderOptions[k.lower()] = urllib2.unquote(str(v))
        
    def getOption(self, optionName):
        return self._getOption(optionName)
    
    def _getOption(self, optionName):
        
        name = optionName.lower()

        if name not in self._slabOptionsLookup:
            log.warning("Unknown option %s received, returning None" % (name,))
            return None
        
        value = None;
        if name in self._renderOptions:
            value = self._getOptionFromDict(name)
        
        if value == None:
            value = self._getDefaultForOption(name)
        
        return value
    
    def _getOptionFromDict(self, optionName):
        
        value = None
        
        try:
            stringValue = self._renderOptions[optionName]
            type = self._slabOptionsLookup[optionName].type
            log.debug("optionName = %s, stringValue = %s" % (optionName, stringValue,))
            
             
            
            if type == bool :
                value = stringValue.lower() == 'true'
            else:
                value = type(stringValue)
                
            renderOpt = self._slabOptionsLookup[optionName]
            
            if not renderOpt.options is None:
                if value not in renderOpt.options:
                    log.debug("value %s not in options %s" % (value, renderOpt.options,))
                    value = None

        except:
            log.exception("Error getting option %s from renderOptions=%s" % (optionName, self._renderOptions))
            value = None
            
        return value

    def _getDefaultForOption(self, optionName):
        return self._slabOptionsLookup[optionName].default
        