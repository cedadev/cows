# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
implementation of ILayerMapper, IwfsLayer, IDimension, ILayerSlab interfaces, as defined in wfs_iface.py & wxs_iface.py

"""
import cows.service.imps.csmlbackend.wfs_csmlstoredqueries as CSMLQueries
from cows.service.imps.csmlbackend.csmlcommon import CSMLLayerMapper, CSMLConnector
from cows.service.wfs_iface import *
from cows.model.storedquery import *
import csml.parser
from xml.etree import ElementTree as etree
from shapely.geometry import Polygon, Point
from cows.bbox_util import union
from csml.csmllibs.csmlextra import listify, stringify, cleanString2

import logging
log = logging.getLogger(__name__)

class CSMLwfsLayerMapper(CSMLLayerMapper):
    """
    Map keyword arguments to a collection of layers.
    Supports the retrieval of sets of layers according to arbitrary
    keyword/value pairs.
    Implements  ILayerMapper (does it? TODO: check)
    
    WFS differs from WMS/WCS in that the 'layers' are feature types, not instances.
    So the CSMLwfsLayerMapper map method returns both a map of feature types and a map
    of feature instances as both are needed for the GetFeature method to work.
    
    """
    def __init__(self):
        super(CSMLwfsLayerMapper, self).__init__()
        self.featureinstancecache={}
        self.queryDescriptions=CSMLStoredQueries()
    

    def map(self, **kwargs):
        """
        Given csml.parser.Dataset object list the names of
        all layers available.
        
        :return: A mapping of layer names to ILayer implementations.
        @raise ValueError: If no layers are available for these keywords. 
        """
        fileoruri=kwargs['fileoruri']
        if fileoruri in self.layermapcache.keys():
            #we've accessed this layer map before, get it from the cache dictionary
            return self.layermapcache[fileoruri], self.featureinstancecache[fileoruri]
         
        ds = self.connector.getCsmlDoc(fileoruri)
        try:
            self.datasetName=ds.name.CONTENT
        except AttributeError:
            self.datasetName = 'CSML WFS Service'
        
        #The WFS differs from WMS & WCS in that the contents layer is a list of 
        #feature *types* not *instances*. However a record of instances is also 
        #needed to fulfil GetFeature requests:
        featureset=CSMLFeatureSet() #holds feature instances                
        layermap={} #feature types       
        aggregatedBBoxes={}#for aggregations of bounding boxes.
        

        for feature in csml.csmllibs.csmlextra.listify(ds.featureCollection.featureMembers):
            title, abstract=self.getInfo(feature)
            featureset.featureinstances[feature.id]=CSMLFeatureInstance(title, abstract, feature)             
        for id, instance in featureset.featureinstances.iteritems():
            ftype=instance.featuretype #namespaced type e.g. 'csml:PointSeriesFeature'
            if ftype not in layermap.keys():
                layermap[ftype]=CSMLwfsLayer(ftype, instance.wgs84BBox)
                #instantiate an aggregator to compare future bounding boxes with.
                aggregatedBBoxes[ftype]= instance.wgs84BBox               
            else:
                #the featuretype has already been stored in the dictionary.
                #but, the bounding box may need changing to accommodate this new feature instance.
#                log.debug('Checking bbox for feature id: %s and title: %s'%(instance._feature.id, instance.title))
                currentbbox=aggregatedBBoxes[ftype]
                newbbox=union(currentbbox, instance.wgs84BBox)
                aggregatedBBoxes[ftype]= newbbox
                layermap[ftype]=CSMLwfsLayer(ftype, newbbox)
            

        if len(layermap) > 0:
            #cache results
            self.layermapcache[fileoruri]=layermap
            self.featureinstancecache[fileoruri]=featureset
            return layermap, featureset
        else:
            raise ValueError

class CSMLStoredQueries(object):
    """ Holds definitions of supported WFS stored queries and mappings to functional implementations"""
    def __init__(self):
        #self.queries is a dictionary of form: {id:(StoredQuery, func)}
        #where func is the name of the implementation of the stored query (typically) in wfs_csmlstoredqueries      
        self.queries={}
        
        #simple example query
        qid='queryOne'        
        qet=QueryExpressionText('xyzml:SomeFeatureType') 
        pex1=ParameterExpression('arg1', 'xsd:string')
        pex2=ParameterExpression('arg2', 'xsd:string')
        query=StoredQuery(qid, title='test query', abstract = 'my test query', queryExpressionText = qet, parameter=[pex1, pex2])
        self.queries[qid]=(query, CSMLQueries.query_one_func)
     
         
        #mandatory get feature by id
        qid='urn-x:wfs:StoredQueryId:ISO:GetFeatureById'
        qet=QueryExpressionText('csml:AbstractFeature')
        pex=ParameterExpression('id', 'xsd:anyURI')
        query=StoredQuery(qid, title='GetFeatureById', abstract = 'Get any feature by id', queryExpressionText = qet, parameter=[pex])
        self.queries[qid]=(query, CSMLQueries.query_getFeatureById)

        #query to select features by phenomenon
        qid='urn-x:wfs:StoredQueryId:badc.nerc.ac.uk:phenomenonQuery'
        qet=QueryExpressionText('csml:AbstractFeature')#TODO, this could definitely differ for different features...
        pex=ParameterExpression('phenomenon', 'xsd:string')
        query=StoredQuery(qid, title='SelectFeaturesByPhenomenon', abstract = 'Select features based on their phenomenon type, e.g. "temperature"', queryExpressionText = qet, parameter=[pex])
        self.queries[qid]=(query, CSMLQueries.query_getFeatureByPhenomenon)
        
        #query to extract a PointFeature from a PointSeriesFeature
        qid='urn-x:wfs:StoredQueryId:badc.nerc.ac.uk:extractPointFromPointSeries'
        qet=QueryExpressionText('csml:PointFeature')
        pex1=ParameterExpression('featureid', 'xsd:anyURI')
        pex2=ParameterExpression('timeinstance', 'gml:TimePositionUnion')
        query=StoredQuery(qid, title='ExtractPointFromPointSeries', abstract = 'Extract a csml:PointFeature for a single time instance from a csml:PointSeriesFeature', queryExpressionText = qet, parameter=[pex1, pex2])
        self.queries[qid]=(query, CSMLQueries.query_extractPointFromPointSeries)

        #query to extract a PointSeriesFeature from a PointSeriesFeature
        qid='urn-x:wfs:StoredQueryId:badc.nerc.ac.uk:extractPointSeriesFromPointSeries'
        qet=QueryExpressionText('csml:PointSeriesFeature')
        pex1=ParameterExpression('featureid', 'xsd:anyURI')
        pex2=ParameterExpression('mintime', 'gml:TimePositionUnion')
        pex3=ParameterExpression('maxtime', 'gml:TimePositionUnion')
        query=StoredQuery(qid, title='ExtractPointSeriesFromPointSeries', abstract = 'Extract a csml:PointSeriesFeature for a range of times from a csml:PointSeriesFeature', queryExpressionText = qet, parameter=[pex1, pex2, pex3])
        self.queries[qid]=(query, CSMLQueries.query_extractPointSeriesFromPointSeries)

        #query to extract a GridSeriesFeature from a GridSeriesFeature
        qid='urn-x:wfs:StoredQueryId:badc.nerc.ac.uk:extractGridSeriesFromGridSeries'
        qet=QueryExpressionText('csml:GridSeriesFeature')
        pex1=ParameterExpression('featureid', 'xsd:anyURI')
        pex2=ParameterExpression('mintime', 'gml:TimePositionUnion')
        pex3=ParameterExpression('maxtime', 'gml:TimePositionUnion')
        pex4=ParameterExpression('bbox', 'xsd:string')
        paramlist=[pex1,pex2,pex3, pex4]
        query=StoredQuery(qid, title='ExtractGridSeriesFromGridSeries', abstract = 'Extract a csml:GridSeries from a csml:GridSeriesFeature', queryExpressionText = qet, parameter=paramlist)
        self.queries[qid]=(query, CSMLQueries.query_extractGridSeriesFromGridSeries)

        #query to extract a PointSeriesFeature from a GridSeriesFeature
        qid='urn-x:wfs:StoredQueryId:badc.nerc.ac.uk:extractPointSeriesFromGridSeries'
        qet=QueryExpressionText('csml:PointSeriesFeature')
        pex1=ParameterExpression('featureid', 'xsd:anyURI')
        pex2=ParameterExpression('mintime', 'gml:TimePositionUnion')
        pex3=ParameterExpression('maxtime', 'gml:TimePositionUnion')
        pex4=ParameterExpression('latitude', 'xsd:string')
        pex5=ParameterExpression('longitude', 'xsd:string')
        paramlist=[pex1,pex2,pex3, pex4, pex5]
        query=StoredQuery(qid, title='ExtractPointSeriesFromGridSeries', abstract = 'Extract a csml:PointSeries from a csml:GridSeriesFeature', queryExpressionText = qet, parameter=paramlist)
        self.queries[qid]=(query, CSMLQueries.query_extractPointSeriesFromGridSeries)
        

class CSMLFeatureSet(IFeatureSet):
    """ A set of features available via a WFS. Supports querying methods as used by OGG filters """
    def __init__(self):
        self.featureinstances={}

    def getFeatureList(self):
        results=[]
        for featureid,feature in self.featureinstances.iteritems():
            results.append(feature)
        return results

    def getFeatureByGMLid(self, gmlid):
        return self.featureinstances[gmlid]
    
    def _checkforOverlap(self, filterbbox, featurebbox):
        """ Uses Shapely Polygons to calculate bounding box intersections """
        log.debug('comparing against %s'%str(filterbbox))        
        filterpolygon=Polygon(((filterbbox[0],filterbbox[1]),(filterbbox[0],filterbbox[3]),(filterbbox[2],filterbbox[3]),(filterbbox[2],filterbbox[1])))
        featurepolygon=Polygon(((featurebbox[0],featurebbox[1]),(featurebbox[0],featurebbox[3]),(featurebbox[2],featurebbox[3]),(featurebbox[2],featurebbox[1])))        
        log.debug(dir(filterpolygon))
        log.debug('intersect result%s'%featurepolygon.intersects(filterpolygon))
        return filterpolygon.intersects(featurepolygon)
    
    def _checkforPointinBox(self, filterbbox, location):
        """ Uses Shapely Polygons to calculate bounding box intersections """
        log.debug('comparing against %s'%str(filterbbox))        
        filterpolygon=Polygon(((filterbbox[0],filterbbox[1]),(filterbbox[0],filterbbox[3]),(filterbbox[2],filterbbox[3]),(filterbbox[2],filterbbox[1])))
        featurepoint=Point(float(location[0]), float(location[1]))
        log.debug(featurepoint.within(filterpolygon))
        log.debug('intersect result%s'%featurepoint.intersects(filterpolygon))
        return featurepoint.intersects(filterpolygon)
    
    def getFeaturesByBBox(self,bboxtuple, srsname):          
        log.debug('GET FEATURES BY BBOX')
        result=[]
        log.debug('Request BBOX: %s %s'%(bboxtuple,srsname))
        for featureid,feature in self.featureinstances.iteritems():
            if hasattr(feature._feature, 'boundedBy'):
                log.debug('Checking bbox for feature %s: '%feature._feature.id)
                lowercorner=feature._feature.boundedBy.lowerCorner.CONTENT.split()
                uppercorner=feature._feature.boundedBy.upperCorner.CONTENT.split()
                featurebbox=(float(lowercorner[0]), float(lowercorner[1]), float(uppercorner[0]), float(uppercorner[1]))                
                if self._checkforOverlap(bboxtuple, featurebbox):
                    result.append(feature)  
            elif hasattr(feature._feature, 'location'):
                log.debug('Checking location for feature %s: '%feature._feature.id)
                log.debug(feature._feature.location)
                location=feature._feature.location.CONTENT.split()
                if self._checkforPointinBox(bboxtuple, location):
                    result.append(feature)                        
        return result

    def getFeaturesByPropertyBetween(self, propertyname, minvalue, maxvalue):
        log.debug('GET FEATURES BY PropertyBetween')
        log.debug('propertyname, min, max: %s, %s, %s'%(propertyname, minvalue, maxvalue))
        result = []
        #Identifies times overlapping between filter and feature times
        if propertyname=='csml:value/csml:PointSeriesCoverage/csml:pointSeriesDomain/csml:TimeSeries/csml:timePositionList':
            for featureid, feature in self.featureinstances.iteritems():
                featuretimes=feature._feature.value.pointSeriesDomain.timePositionList.CONTENT.split()
                featureMinTime=featuretimes[0]
                featureMaxTime=featuretimes[len(featuretimes)-1]
                if csml.csmllibs.csmltime.compareTimes(featureMinTime, minvalue ,featureMaxTime) == 1:
                    result.append(feature)
                elif csml.csmllibs.csmltime.compareTimes(featureMinTime, maxvalue ,featureMaxTime) == 1:
                    result.append(feature)    
        return result
        
    def getFeaturesByPropertyEqualTo(self, propertyname, value):
        log.debug('GET FEATURES BY PropertyEqualTo, value=%s'%value)
        result=[]
        value=value #value may be unicode
        if propertyname == 'csml:parameter':
            log.debug('filtering on csml:parameter')          
            for featureid,feature in self.featureinstances.iteritems():
                if feature._feature.parameter.getStandardName() == value:
                    result.append(feature)      
                elif feature._feature.parameter.getNonStandardName() == value:                    
                    result.append(feature) 
            return result
    
class CSMLFeatureInstance(IFeatureInstance):
    def __init__(self, title, abstract, feature):
        """ representing a CSML Feature Instance 
        :ivar title: The title of the feature instance
        :ivar abstract: The abstract of the feature instance
        :ivar feature: the csml feature instance object 
         """
        self.title=title
        self.abstract=abstract
        self._feature=feature
        self.featuretype='csml:'+self._feature.__class__.__name__
        try:
            bb= self._feature.getCSMLBoundingBox().getBox()
            #convert 0 - 360 to -180, 180 as per common WMS convention
            if abs(bb[2]-bb[0]) >= 359 and abs(bb[2]-bb[0]) < 361:
                bb[0], bb[2]=-180, 180
            self.wgs84BBox = bb
        except AttributeError:
            log.debug('there is a problem getting the bounding box for feature id %s'%self._feature.id)
            self.wgs84BBox=()
    
    def _fixXlinks(self):
        ''' replaces xlinks in feature domain with inline content'''
        for att in ['gridSeriesDomain', 'pointDomain', 'profileSeriesDomain','sectionDomain','trajectoryDomain']:
            if hasattr(self._feature.value, att):
                domain=getattr(self._feature.value,att)
                if hasattr(domain, 'coordTransformTable'):
                    for ordinate in listify(domain.coordTransformTable.gridOrdinates):
                        #insertedExtract is the 'hidden' resolved xlink data, expose inline
                        if hasattr(ordinate.coordAxisValues, 'insertedExtract'):
                            ordinate.coordAxisValues.CONTENT=cleanString2(str(ordinate.coordAxisValues.insertedExtract.getData()[0].tolist()))                            
    
    def toGML(self):
        """ Create a GML (CSML) representation of the feature """
        nonamespaceFType=self.featuretype.split(':')[1] #remove the csml: prefix
        qualifiedFeatureType='{http://ndg.nerc.ac.uk/csml}' + nonamespaceFType
        emptyelem=etree.Element(qualifiedFeatureType)
        #modify self._feature so that any references to xlinks are replaced with inline content
        self._fixXlinks()        
        csmlelem=self._feature.toXML(emptyelem)
        return etree.tostring(csmlelem)
        
        
      
class CSMLwfsLayer(IwfsLayer):
    """ representing a WFS FeatureType (termed layer here). Implements IwfsLayer
    :ivar featuretype: The namespaced name of the feature type, e.g. csml:PointSeriesFeature
    
    """
    def __init__(self, featuretype, wgs84bb):
        self.type=featuretype
        #Have to hard code some definitions for CSML feature types to 
        #use in the capabilities document as they don't exist anywhere else.
        #Hardcoding is okay as this is a CSML specific interface, so will only ever deal
        #with CSML feature types.
        #TODO: However, might be better to move to some sort of schema.cfg file?
        self.wgs84BBox=wgs84bb     
        self.outputformats=['text/xml: subtype=csml/2.0']    
        if self.type=='csml:GridSeriesFeature':
            self.title='GridSeriesFeature as defined in Climate Science Modelling Language.'
            self.abstract='The CSML GridSeriesFeature is used to represent 4D gridded data such as atmospheric model output.'
            self.keywords=['Grid', 'Climate', 'CSML']
        elif self.type=='csml:PointSeriesFeature':
            self.title='PointSeriesFeature as defined in Climate Science Modelling Language.'
            self.abstract='The CSML PointSeriesFeature represents a time series of measurements at a single point in space.'
            self.keywords=['Point', 'Timeseries', 'Climate', 'CSML']
        #TODO: definitions for all feature types.
        
        


