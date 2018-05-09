# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import logging
import simplejson as json

log = logging.getLogger(__name__)

class SlabJSONGenerator(object):
    
    def __init__(self, styleOptionsMap):
                
        self.commonOptions = []
        self.styleOptions = {}
        
        #for each of the styles mentioned
        for style in styleOptionsMap.keys():
            
            #create an empty list to hold each styles specific options
            self.styleOptions[style] = []
            
            #for each of the options in this style
            for option in styleOptionsMap[style]:
                
                #check if this option appears in all the others 
                isCommon = True
                for styleNames in styleOptionsMap.values():
                    if option.name not in styleNames:
                        isCommon = False
                
                #add the option to one of the lists
                if isCommon:
                    if option.name not in [x.name for x in self.commonOptions]:
                        self.commonOptions.append(option)
                else:
                    self.styleOptions[style].append(option)
            
        
    def generateJSON(self):

        displayOptions = {}
        
        displayOptions['common'] = self._buildOptionsList(self.commonOptions)
        
        for style, optionsList in self.styleOptions.items():
            displayOptions[style] = self._buildOptionsList(optionsList)
            
        return json.dumps(displayOptions)

    def _buildOptionsList(self, optionsList):
        
        list = [self._buildOptionDict(opt) for opt in optionsList]
            
        return list
    
    def _buildOptionDict(self, renderOption):
        
        optionDict = {}
        optionDict['name'] = renderOption.name
        optionDict['title'] = renderOption.title
        optionDict['defaultVal'] = renderOption.default
        
        if optionDict['defaultVal'] == None:
            optionDict['defaultVal'] = ''
        
        if renderOption.options != None:
            optionDict['options'] = renderOption.options
            optionDict['type'] = 'select'
            
        elif renderOption.type == bool:
            optionDict['type'] = 'bool'
            
        else:
            optionDict["type"] ="value"
        
        return optionDict