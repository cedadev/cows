# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
The classes in this module define an interface between the OWS Pylons
server and components that provide Web Feature Server layers. They
extend the interfaces defined in wxs_iface.py.


"""

from wxs_iface import ILayer

        

class IwfsLayer(ILayer):
    """
    An interface representing a WFS FeatureType, based on ILayer.
    :ivar keywords: describing this feature type.
    :ivar outputformats: list of output formats available for this feature type.
    """
    keywords=outputformats=NotImplemented

class IFeatureSet(object):
    """ A set of features available via a WFS. Supports querying methods as used by OGG filters 
    :ivar featureinstances: feature instances available in this feature set"""

    def getFeatureByGMLid(self, gmlid):
        """ return a feature specified by gmlid 
        :return: zero or one IFeatureInstance
        """
        raise NotImplementedError
    
    def getFeaturesByBBox(self,bboxtuple, srsname):
        """ return features within a bbox (llx, lly, urx, ury) in a particular srs
        :return: zero or more IFeatureInstance 
        """
        raise NotImplementedError

    
    def getFeaturesByTemporalRange(self, range):
        """ return features within a temporal range (minT, maxT) in form YYYY-MM-DDT00:00:00.0
        :return: zero or more IFeatureInstance 
        """
        raise NotImplementedError    
    
        
class IFeatureInstance(object):
    """     An interface representing a feature (as defined in a GML application schema)
    :ivar title: title of feature instance
    :ivar abstract: abstract of feature instance 
    :ivar feature: feature instance 
    """ 
    
    type=title=abstract=NotImplemented
    
    def toGML(self):
        """ return a GML representation of the feature as a string 
        :return: string of GML
        """
        raise NotImplementedError
