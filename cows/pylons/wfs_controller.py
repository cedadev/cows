# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
WFS controller for OGC Web Services (OWS).

@author: Dominic Lowe
"""

import re
from cStringIO import StringIO
from sets import Set
from pylons import request, response
from pylons import tmpl_context as c
import ConfigParser
import xml.etree.ElementTree as etree
import logging
log = logging.getLogger(__name__)


from cows.model.wfs import WfsFeatureSummary
from cows.model.filterencoding import FEQueryProcessor
from cows.model import PossibleValues, WGS84BoundingBox, BoundingBox, Contents
from cows.pylons import ows_controller
from cows.exceptions import *
from cows import bbox_util
from cows.service.imps.csmlbackend.config import config
from cows.service.imps.csmlbackend.wfs_csmllayer import CSMLFeatureSet

class WFSController(ows_controller.OWSController):
    """
    Subclass this controller in a pylons application and set the layerMapper
    class attribute to implement a WFS. Each layer can be mapped to a Feature for the WFS.

    @cvar layerMapper: an cows.service.wxs_iface.ILayerMapper object. 
    

    """
    layerMapper = None
    _layerSlabCache = {}

    #-------------------------------------------------------------------------
    # Attributes required by OWSController

    service = 'WFS'
    owsOperations = (ows_controller.OWSController.owsOperations + ['DescribeFeatureType', 'GetFeature', 'DescribeStoredQueries','ListStoredQueries', 'GetPropertyValue'])
    validVersions = ['1.1.0', '2.0.0']
    

    #-------------------------------------------------------------------------

    def __before__(self, **kwargs):
        """
        This default implementation of __before__() will pass all routes
        arguments to the layer mapper to retrieve a list of layers for
        this WFS.

        It will be called automatically by pylons before each action method.


        """
        log.debug('loading layers')
        wfsBlacklist=[]        
        
        configFile = config.get('wfsBlacklist')
        log.debug(configFile)
        if configFile:
            try:
                conf=ConfigParser.ConfigParser()
                conf.read(configFile)
                wfsBlacklist=conf.get('Blacklist', 'donotserve').split()    
            except (ConfigParser.NoOptionError,ConfigParser.NoSectionError):
                pass
        log.debug('WFS blacklist %s'%wfsBlacklist)
        if kwargs['fileoruri'] in wfsBlacklist:
            log.debug('wfs blacklisting %s'%kwargs['fileoruri'] )
            self.layers={}
            self.featureset=CSMLFeatureSet() #return dummy layers and featureset
        else:
            self.layers, self.featureset = self.layerMapper.map(**kwargs)
            log.debug('Feature instances %s'%self.featureset.featureinstances)
               
        
        
        #-------------------------------------------------------------------------
        # Methods implementing stubs in OWSController

    def _renderCapabilities(self, version, format):
        """
        Renders capabilities document.
        """
        if version == '1.1.0':
            t = ows_controller.templateLoader.load('wfs_capabilities_1_1_0.xml')
        elif version == '2.0.0':
            t = ows_controller.templateLoader.load('wfs_capabilities_2_0_0.xml')
        else:
            # We should never get here!  The framework should raise an exception before now.
            raise RuntimeError("Version %s not supported" % version)
        
        return t.generate(c=c).render()

    def _loadCapabilities(self):
        """
        @note: Assumes self.layers has already been created by __before__().
        Builds capabilities document.

        """
        log.info('Loading WFS Capabilites')
        
        ows_controller.addOperation('GetFeature')
        ows_controller.addOperation('DescribeFeature')
        ows_controller.addOperation('DescribeStoredQueries')
        ows_controller.addOperation('ListStoredQueries')
        ows_controller.addOperation('GetPropertyValue')
        
        
        featureInfoFormats = Set()

        log.debug('Loading capabilities contents')
        c.capabilities.contents = Contents()
        
        
        ftlist={}
        #        
        
        for layerName, layer in self.layers.items():
            log.info('Loading layer %s' % layerName)
#            log.info('feature type %s'%layer._feature)

            wgs84BBox = WGS84BoundingBox(layer.wgs84BBox[:2],
                                         layer.wgs84BBox[2:])
            
            ds = WfsFeatureSummary(keywords=layer.keywords, 
                                   outputformats=layer.outputformats, 
                                   identifier=layerName,
                                   titles=[layer.title],
                                   abstracts=[layer.abstract],                                   
                                   wgs84BoundingBoxes=[wgs84BBox])

            c.capabilities.contents.datasetSummaries.append(ds)
        
        #LayerMapper may optionally implement a datasetName attribute which 
        #will be tried if serviceIdentification/title is not supplied in capabilities config
        if c.capabilities.serviceIdentification.titles[0] is None:
            try:
                c.capabilities.serviceIdentification.titles=[self.layerMapper.datasetName]
            except AttributeError:
                pass

    def _getSchema(self, typename):
        namespace = typename.split(':')[0]
        schemalocation = conf
        
    def _parsetypename(self, typename):
        """ parse feature type name into schema and name and return schema"""       
        if typename not in self.layers.keys():
            raise InvalidParameterValue('Invalid typename parameter: %s. Typename must consist of namespace and featuretype separated with a colon, as displayed in the GetCapabilities response.'%typename, 'typename')
    
        namespace, ft = typename.split(':')
        wfsconfiglocation=config['wfsconfig']
        wfscfg = ConfigParser.ConfigParser()
        wfscfg.read(wfsconfiglocation)      
        xmlschema=open(wfscfg.get('application_schemas', namespace)).read()      
        log.debug('location of application schema %s' %(xmlschema))
        return xmlschema
    
    def _runQuery(self, queryxml = None, storedqueryid=None, typename=None, maxfeatures=None,**kwargs):
        """ this is used by both the GetFeature and GetPropertyValue methods to
        run a wfs:query over a featurecollection and return a subset of the collection. 
        The query may be defined as an xml <wfs:query> or may be referenced by a StoredQuery_id 
        """
        additionalobjects=[] #not implemented for filter encoding, just for storedqueries (e.g. subsetting)
        if queryxml:
            qp=FEQueryProcessor()
            log.info('Sending query: %s to query processor '%queryxml)
            resultset=qp.evaluate(self.featureset, queryxml)
            log.info('Final resultset from query processor %s'%resultset)
        elif storedqueryid:
            storedquery, func=self.layerMapper.queryDescriptions.queries[storedqueryid]
            storedqueryresult=func(self.featureset, **kwargs)
            if len(storedqueryresult) == 2:
                resultset=storedqueryresult[0]
                additionalobjects=storedqueryresult[1]
            else:
                resultset=storedqueryresult
            log.debug('Final resultset from stored query %s'%resultset)
        else:           
            #If neither query or storedquery_id are provided then return entire featureset, filtered on 'typename' and/or 'maxfeatures' if supplied.
            resultset=self.featureset.getFeatureList()
            if typename:
                templist = resultset[:]
                for feature in templist:   #remove any features of the wrong feature type
                    if feature.featuretype != typename:
                        resultset.remove(feature)
                resultset=resultset
                if maxfeatures: #reduce the response to the requested number of feature instances
                    maxf=int(maxfeatures)
                    if len(resultset) >maxf:
                        resultset=resultset[:maxf]
        return resultset, additionalobjects

    def _applyXPath(self, xpath, features):
        """ applies an xpath expression to a set of features and returns 
        a set of wfs:members containing property values expressed in the xpath"""
        resultset=[]        
        #if xpath is looking for an attribute, handle it differently - this should be unnecessary when migrated to element tree 1.3
        #i.e. if of the form /somepath/path[@attribute]
        attstart=xpath.find('[')
        if attstart == -1: #no attribute            
            for feature in features:
                #need to deal with the underlying XML
                #To make sure all xlink references are resolved correctly, convert feature to GML (which calls the CSML toXML() method then read back in with ElementTree
                featureGML=feature.toGML()
                featureXML=etree.fromstring(featureGML)               
                
                valuecomponent=featureXML.find(xpath)
                if valuecomponent is not None:
                    valstr=etree.tostring(valuecomponent)           
                    resultset.append(valstr)
        else:
            #there is an attribute:
            attributeName=xpath.split('[')[1][1:-1]
            xpath=xpath.split('[')[0]
            for feature in features:
                #get the underlying XML
                featureGML=feature.toGML()
                featureXML=etree.fromstring(featureGML)
                log.debug('xpath path %s'%xpath)
                log.debug('attribute %s'%attributeName)
                if len(xpath) ==0:
                    valuecomponent=featureXML
                else:
                    valuecomponent=featureXML.find(xpath)
                log.debug('valuecomponent %s'%valuecomponent)
                if valuecomponent is not None:
                    attribute=valuecomponent.get(attributeName)         
                    resultset.append(attribute)            
        log.debug(resultset)
        return resultset      
    
    
    def DescribeFeatureType(self):
        """ DescribeFeatureType """
        version = self.getOwsParam('version', default=self.validVersions[0])
        if version not in self.validVersions:
            raise InvalidParameterValue('Version %s not supported' % version,
                                        'version')
        typename=self.getOwsParam('typename')
        ftschema =self._parsetypename(typename)
        log.debug(self.layers.items())       
               
        outputformat=self.getOwsParam('outputformat', default='text/xml')
        
        #temporarily returns entire schema
        #TODO: return single featuretype definition
        msg  = ftschema
        response.headers['content-type'] = 'text/xml'
        return msg
            
  
    def GetPropertyValue(self):
        """ GetPropertyValue request - similar to get feature but only returns chosen property
        values """
        valueReference = self.getOwsParam('valueReference')
        queryxml=self.getOwsParam('query',default=None)
        storedqueryid=self.getOwsParam('storedquery_id', default=None)
        typename=self.getOwsParam('typename', default=None)
        #get any other parameters from self._owsParams and pass them to the stored query
        otherparams={}
        for key in self._owsParams.keys():
            if key not in ['query', 'request', 'service', 'version', 'storedquery_id', 'typename', 'valuereference']:
                otherparams[key]=self._owsParams[key]     
        featureresultset, additionalobjects =self._runQuery(queryxml, storedqueryid, typename, **otherparams)        
       
        #Now need to take account of valueReferencexpath, and distill the 
        #resultset down to just the requested properties.
        c.resultset=self._applyXPath(valueReference, featureresultset)
        
        response.headers['content-type'] = 'text/xml'
        #TODO, new template for values
        t = ows_controller.templateLoader.load('wfs_valuecollection.xml')
        return t.generate(c=c).render() 
  
    def GetFeature(self):
        """ GetFeature request
        """
        log.info('GET FEATURE Request made: %s'%request)
        version = self.getOwsParam('version', default=self.validVersions[0])
        if version not in self.validVersions:
            raise InvalidParameterValue('Version %s not supported' % version,
                                        'version')

        #The GetFeature request may either use the 'query' filter encoding or a 
        #storedquery, but not both:      
        #Parse the query to analyse the filters it contains
        queryxml=self.getOwsParam('query',default=None)
        storedqueryid=self.getOwsParam('storedquery_id', default=None)
        typename=self.getOwsParam('typename', default=None)
        maxfeatures=self.getOwsParam('maxfeatures', default=None)
       
        #retrieve any other parameters and pass them off to the stored query (they are ignored in the case of the queryxml option
        otherparams={}
        for key in self._owsParams.keys():
            if key not in ['query', 'request', 'service', 'version', 'storedquery_id', 'typename', 'maxfeatures']:
                otherparams[key]=self._owsParams[key]       
        c.resultset, c.additionalobjects=self._runQuery(queryxml, storedqueryid, typename, maxfeatures, **otherparams)
               
        #Group resultset together in a wfs feature collection (use template)
        response.headers['content-type'] = 'text/xml'
        t = ows_controller.templateLoader.load('wfs_featurecollection.xml')
        return t.generate(c=c).render()            

   
    def DescribeStoredQueries(self):
        """ DescribeStoredQueries method. Takes zero or more stored query ids as args"""
        allqueries=self.layerMapper.queryDescriptions.queries        
        storedqueryid=self.getOwsParam('storedqueryid', default=None)
        if storedqueryid is None:
            c.storedqueries = self.layerMapper.queryDescriptions.queries
        else:
            c.storedqueries={}
            for queryid in storedqueryid.split(','):
                c.storedqueries[queryid]=self.layerMapper.queryDescriptions.queries[queryid]       
        response.headers['Content-Type'] = 'text/xml'
        t = ows_controller.templateLoader.load('wfs_describestoredqueries.xml')
        return t.generate(c=c).render()  
         
    def ListStoredQueries(self):
        """ DescribeStoredQueries method. Takes zero or more stored query ids as args"""
        c.storedqueries = self.layerMapper.queryDescriptions.queries
        t = ows_controller.templateLoader.load('wfs_liststoredqueries.xml')
        response.headers['Content-Type'] = 'text/xml'
        return t.generate(c=c).render() 
