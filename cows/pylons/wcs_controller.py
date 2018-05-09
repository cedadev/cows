# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
WMS controller for OGC Web Services (OWS).

@author: Stephen Pascoe
"""
    
import re, os
import math
from cStringIO import StringIO
from sets import Set
from matplotlib.cm import get_cmap
from pylons import request, response
from pylons import tmpl_context as c
import paste

import logging
log = logging.getLogger(__name__)


from genshi.template import TextTemplate

from cows.model.wms import Dimension
from cows.model.wcs import WcsDatasetSummary, CoverageDescription
from cows.model import PossibleValues, WGS84BoundingBox, BoundingBox, Contents
from cows.pylons import ows_controller
from cows.exceptions import *
from cows import bbox_util
import ConfigParser
from cows.service.imps.csmlbackend.config import config

class WCSController(ows_controller.OWSController):
    """
    Subclass this controller in a pylons application and set the layerMapper
    class attribute to implement a WCS.

    @cvar layerMapper: an cows.service.wcs_iface.ILayerMapper object.

    """
    layerMapper = None
    _layerSlabCache = {}

    #-------------------------------------------------------------------------
    # Attributes required by OWSController

    service = 'WCS'
    owsOperations = (ows_controller.OWSController.owsOperations +
        ['GetCoverage', 'DescribeCoverage'])
    validVersions = ['1.0.0']
    

    #-------------------------------------------------------------------------

    def __before__(self, **kwargs):
        """
        This default implementation of __before__() will pass all routes
        arguments to the layer mapper to retrieve a list of coverages for
        this WCS.

        It will be called automatically by pylons before each action method.

        @todo: The layer mapper needs to come from somewhere.

        """
        log.debug("loading layers")
        wcsBlacklist=[]        
        
        configFile = config.get('wcsBlacklist')
        if configFile:
            try:
                conf=ConfigParser.ConfigParser()
                conf.read(configFile)
                wcsBlacklist=conf.get('Blacklist', 'donotserve').split()    
            except (ConfigParser.NoOptionError,ConfigParser.NoSectionError):
                pass
        if kwargs['fileoruri'] in wcsBlacklist:
            log.debug('wcs blacklisting %s'%kwargs['fileoruri'] )
            self.layers={}
        else:
            self.layers = self.layerMapper.map(**kwargs)   

    #-------------------------------------------------------------------------
    # Methods implementing stubs in OWSController

    def _renderCapabilities(self, version, format):
        if version == '1.0.0':
            t = ows_controller.templateLoader.load('wcs_capabilities_1_0_0.xml')
        else:
            # We should never get here!  The framework should raise an exception before now.
            raise RuntimeError("Version %s not supported" % version)
        
        return t.generate(c=c).render()

    def _loadCapabilities(self):
        """
        @note: Assumes self.layers has already been created by __before__().

        """
        ows_controller.addOperation('GetCoverage')
        ows_controller.addOperation('DescribeCoverage')  
        featureInfoFormats = Set()

        log.debug('Loading capabilities contents')
        c.capabilities.contents = Contents()
        
        #TODO, the bounding box may include a Z dimension in WCS.
        for cvgName, coverage in sorted(self.layers.items()):
            log.debug('Loading coverage %s' % cvgName)

#            wgs84BBox = WGS84BoundingBox(coverage.wgs84BBox[:2],
#                                         coverage.wgs84BBox[2:])
#            wgs84BBox=coverage.wgs84BBox
#            # Get CRS/BBOX pairs
#            bboxObjs = []
#            for crs in coverage.crss:
#                bbox = coverage.getBBox(crs)
#                bboxObjs.append(BoundingBox(bbox[:2], bbox[2:], crs=crs))
                
            # Create the cows object
            #From the ows_servers stack - allthese values should come from  the Coverage object.
            #TODO, the bounding box may include a Z dimension in WCS.
            ds = WcsDatasetSummary(identifier=coverage.name,
                                 titles=coverage.title,
                                 wgs84BoundingBoxes=[coverage.wgs84BBox],
                                 boundingBoxes=[coverage.bboxes], 
                                 description=coverage.description,
                                 abstracts=coverage.abstract,
                                 formats=['application/cf-netcdf'],
                                 supportedCRSs=coverage.crss, 
                                 timelimits=coverage.timeLimits
                                 )

            c.capabilities.contents.datasetSummaries.append(ds)
        #LayerMapper may optionally implement a datasetName attribute which 
        #will be tried if serviceIdentification/title is not supplied in capabilities config
        if c.capabilities.serviceIdentification.titles[0] is None:
            try:
                c.capabilities.serviceIdentification.titles=[self.layerMapper.datasetName]
            except AttributeError:
                pass
            
    def _getLayerParam(self, paramName='coverage'):
        """
        Retrieve the layers parameter enforcing the rule of only
        selecting one coverage for now.

        @param paramName: Overrides the query string parameter name to
            look for.  This is usefull for implementing GetFeatureInfo.

        """
        layerName = self.getOwsParam(paramName)

        # Select the first layer if several are requested.
        # This plays nicer with mapClient.
        if ',' in layerName:
            #layerName = layerName.split(',')[0]
            raise InvalidParameterValue(
                'Multi-coverage getCoverage requests are not supported', 'coverage')
        try:
            layerObj = self.layers[layerName]
        except KeyError:
            raise InvalidParameterValue('coverage %s not found' % layerName,
                                        paramName)

        return layerName, layerObj
    
    
    #-------------------------------------------------------------------------
    # OWS Operation methods: DescribeCoverage and GetCoverage
    
    def GetCoverage(self):
        # Housekeeping
        version = self.getOwsParam('version', default=self.validVersions[0])
        if version not in self.validVersions:
            raise InvalidParameterValue('Version %s not supported' % version,
                                        'version')
        # Layer handling
        layerName, layerObj = self._getLayerParam()
        
        # Coordinate parameters
        bbox = tuple(float(x) for x in self.getOwsParam('bbox').split(','))

        srs = self.getOwsParam('crs')

        #if srs not in layerObj.crss:
         #   raise InvalidParameterValue('Layer %s does not support SRS %s' % (layerName, srs))

        # Get format
        format = self.getOwsParam('format')
        if srs not in layerObj.crss:
            raise InvalidParameterValue('Layer %s does not support SRS %s' % (layerName, srs))
        times= self.getOwsParam('time', default=None)
        
        #process times parameter so it is either a single string (one time) or a tuple (range) (OR None)        
        if times is not None:
            if len(times.split(',')) >1:
                times=tuple(times.split(','))
        
        kwargs={}
        for axis in layerObj.axisDescriptions: #TODO - axisDescriptions attribute
            log.debug('axis: %s'%axis.name)
            axisvalues=self.getOwsParam(axis.name, default=None)
            log.debug('values: %s'%axisvalues)
            if axisvalues:
                values=tuple(float(x) for x in axisvalues.split(','))
                if len(values)==1:
                    values=(values[0], values[0],) #set min and max to be equal if single value
                kwargs[axis.name]=values    
        
#     
        filepath = layerObj.getCvg(bbox, time=times, **kwargs) #TODO, refactor so is more flexible (e.g. not just netcdf)
        fileToReturn=open(filepath, 'r')
        mType='application/cf-netcdf'
        response.headers['Content-Type']=mType
        response.headers['Content-Disposition'] = paste.httpheaders.CONTENT_DISPOSITION(attachment=True, filename=filepath)
        u=fileToReturn.read()
        #close and delete file from file system
        fileToReturn.close()
        log.debug('deleting temporary file %s'%filepath)
        os.system('rm %s'%filepath)
        return response.write(u)
        
        
            
    def DescribeCoverage(self):
        c.descriptions=[]
        requestCvg=self.getOwsParam('coverage')
#        super(WCSController, self).GetCapabilities()
        #TODO, the bounding box may include a Z dimension in WCS.
        log.debug('DescribeCoverage request for %s'%requestCvg)
        for cvgName, coverage in self.layers.items():
            log.debug(cvgName)
            if cvgName == requestCvg:
                log.debug('found coverage %s'%cvgName)
                # Create the enhanced Dataset summary for thic coverage
                #TODO, the bounding box may include a Z dimension in WCS.                
                ds = CoverageDescription(identifier=coverage.id,
                                     titles=coverage.title,
                                     wgs84BoundingBoxes=[coverage.wgs84BBox],
                                     boundingBoxes=coverage.bboxes, 
                                     description=coverage.description,
                                     abstracts=coverage.abstract,
                                     formats=['application/cf-netcdf'],
                                     supportedCRSs=coverage.crss, 
                                     timepositions=coverage.timePositions,
                                     timelimits=coverage.timeLimits, 
                                     axisdescriptions=coverage.axisDescriptions)

                c.descriptions.append(ds)
        response.headers['content-type']='text/xml'
        t = ows_controller.templateLoader.load('wcs_describecoverage_1_0_0.xml')
        return t.generate(c=c).render()                




            
