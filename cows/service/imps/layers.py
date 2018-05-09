# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

'''
This class reads the wms configuration XML document, extracts the layer elements specified in the xml file and stores them in a list.  This list of layer elements is used by the WMSLayerMapper class to create a StationLayer object for each layer element in the list, using the information recorded under each layer element.
'''
from xml.etree import cElementTree

class LayerParser(object):

                def __init__(self, file):
                        self.tree = cElementTree.iterparse(file)
                        self.indexList = []
  
                def getLayers (self):
                        layerlist = []

                        for event, elem in self.tree:
                                if elem.tag == "Layer":
                                        curId = elem.findtext("Name")
                                        # checks for duplicate layer name
                                        if self.indexList.count(curId) < 1:
                                                layerlist.append(elem)
                                                self.indexList.append(curId)
                                        else:
                                                raise Exception(str('Duplicate Layer ID: %s')%curId)
                        return layerlist
