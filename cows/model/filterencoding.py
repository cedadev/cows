# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

# Copyright (C) 2008 STFC & NERC (Science and Technology Facilities Council).
# This software may be distributed under the terms of the
# Q Public License, version 1.0 or later.
# http://ndg.nerc.ac.uk/public_docs/QPublic_license.txt

""" Classes to handle filter encoding queries as used in WFS """

from xml.etree import ElementTree as etree
import logging
log = logging.getLogger(__name__)

""" utility functions to save writing out fully qualified names """
nsOGC = 'http://www.opengis.net/ogc'
def OGC(tag):
    return "{"+nsOGC+"}"+tag

nsGML = 'http://www.opengis.net/gml'
def GML(tag):
    return "{"+nsGML+"}"+tag



class AndOperator(object):
    """ Return the intersection of two filters"""
    def __init__(self, elem):
        self.children=elem.getchildren()

    def evaluate(self, featureset):
        qp=QueryProcessor()
        filter=qp.getFilterOrOperator(self.children[0])
        set1=filter.evaluate(featureset)
        filter2=qp.getFilterOrOperator(self.children[1])
        set2=filter2.evaluate(featureset)
        resultset = set1.intersection(set2)
        return resultset
        
        
class OrOperator(object):
    """ Return the union of two filters"""
    def __init__(self, elem):
        self.children=elem.getchildren()

    def evaluate(self, featureset):
        qp=QueryProcessor()
        filter=qp.getFilterOrOperator(self.children[0])
        set1=filter.evaluate(featureset)
        filter2=qp.getFilterOrOperator(self.children[1])
        set2=filter2.evaluate(featureset)
        resultset = set1.union(set2)
        return resultset

#TODO: NOT operator
        
class Filter(object):
    def __init__(self, elem):
        self.elem=elem


class GMLIdFilter(Filter):
    def evaluate(self, featureset):        
        log.debug('Value of gml id filter %s'%self.elem.get(GML('id')))
        resultset=set([featureset.getFeatureByGMLid(self.elem.get(GML('id')))])
        return resultset

class BBoxFilter(Filter):
    def evaluate(self, featureset):
        #parse the bbox xml envelope to get values
        envelope=self.elem.getchildren()[0]
        srsname=envelope.get('srsName')
        lowercorner=envelope.getchildren()[0].text.split()
        uppercorner=envelope.getchildren()[1].text.split()
        bbtuple=(float(lowercorner[0]),float(lowercorner[1]), float(uppercorner[0]), float(uppercorner[1]))
        resultset=set(featureset.getFeaturesByBBox(bbtuple, srsname))                              
        return resultset        

class PropertyIsEqualTo(Filter):
    def evaluate(self,featureset):      
        propname, literal = self.elem.getchildren()
        resultset=set(featureset.getFeaturesByPropertyEqualTo(propname.text, literal.text))
        return resultset
        
class PropertyIsBetween(Filter):
    def evaluate(self, featureset):
        #TODO finish property between        
        lowerbound=upperbound=propertyname=None
        for child in self.elem.getchildren():
            log.debug(child.tag)
            if child.tag == OGC('PropertyName'):
                propertyname=child.text
            elif child.tag == OGC('LowerBoundary'):
                lowerbound=child.getchildren()[0].text
            elif child.tag == OGC('UpperBoundary'):
                upperbound=child.getchildren()[0].text
        resultset=set(featureset.getFeaturesByPropertyBetween(propertyname, lowerbound, upperbound))
        return resultset
                      
class FEQueryProcessor(object):
    def __init__(self):
        pass
    
    def evaluate(self, featureset, queryxml):
        self.rootelem=etree.fromstring(queryxml)
        log.debug('filter root element %s'%self.rootelem)
        log.debug('child elements %s'%self.rootelem.getchildren())
        filterelem=self.rootelem.getchildren()[0]
        resultset=set()
        for filterdef in filterelem.getchildren():
            filter=self.getFilterOrOperator(filterdef)
            filterresult=filter.evaluate(featureset)
            resultset=resultset.union(filterresult)
        return resultset
    
    def getFilterOrOperator(self, filterelem):
        if filterelem.tag=='And':
            f=AndOperator(filterelem)
        elif filterelem.tag=='Or':
            f=OrOperator(filterelem)
        elif filterelem.tag ==OGC('GmlObjectId'):
            f=GMLIdFilter(filterelem)
        elif filterelem.tag ==OGC('BBOX'):
            f=BBoxFilter(filterelem)
        elif filterelem.tag ==OGC('PropertyIsEqualTo'):
            f=PropertyIsEqualTo(filterelem)
        elif filterelem.tag ==OGC('PropertyIsBetween'):
            f=PropertyIsBetween(filterelem)
        log.debug('Filter tag = %s'%filterelem.tag)
        return f
        

            