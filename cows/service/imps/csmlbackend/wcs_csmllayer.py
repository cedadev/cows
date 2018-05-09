# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
implementation of ILayerMapper, IwmsLayer, IwmsDimension, ILayerSlab interfaces, as defined in wms_iface.py & wxs_iface.py

"""
import os, string
import csml
try:
    import cdms2 as cdms
except:
    import cdms
from copy import copy

import logging
log = logging.getLogger(__name__)

from cows.model.wcs import WcsDatasetSummary
from cows.model.common import BoundingBox, WGS84BoundingBox
from cows.service.imps.csmlbackend.csmlcommon import CSMLLayerMapper, CSMLConnector, extractToNetCDF


class CSMLwcsCoverageMapper(CSMLLayerMapper): 
    """
    Map keyword arguments to a collection of layers (coverages)
    Supports the retrieval of coverages according to arbitrary
    keyword/value pairs.  
    """
    def __init__(self):
        super(CSMLwcsCoverageMapper, self).__init__()
       
    
    def getInfo(self, feature):
        ''' given a csml feature, return info about the layer/feature
        @return:   title, abstract, units, crss '''

        title, abstract = super(CSMLwcsCoverageMapper, self).getInfo(feature)
        units=feature.getDomainUnits()
        tmpunits=copy(units)
        tmpunits.reverse()
        domain = feature.getDomain()
        tax= feature.getTimeAxis()
        
        try:
            timepositions=domain[tax]
            timelimits=[domain[tax][0]+'Z',domain[tax][len(domain[tax])-1]+'Z']
        except: #no time available, return empty strings
            timepositions=['']
            timelimits=['',''] 
            
        crs=feature.getNativeCRS()
        log.debug('crs %s'%crs)
        crss=[self._crscat.getCRS(crs).twoD] 
        if 'EPSG:4326' in crss:
            crss.append('CRS:84')
            crss.append('WGS84')
        log.debug('crss %s'%crss)
        #build definitions of any Z axes such as air_pressure:
        axisDescriptions=[]        
        lon=feature.getLongitudeAxis()
        lat=feature.getLatitudeAxis()
        t=feature.getTimeAxis()
        
        if None in [lon, lat, t]:
            #TODO need to return a suitable wcs error.
            log.debug('warning, could not get correct axis info')
            #best guess!
            if t is None:
                t='time'
            if lon is None:
                lon = 'longitude'
            if lat is None:
                lat = 'latitude'
                
        
        #get the valid values for the Z dimension e.g. the available pressure levels
        for ax in feature.getAxisLabels():
            if ax not in [lat, lon, t]:
                name=label=ax
                domain=feature.getDomain()
                values=domain[name].tolist()
                axis=AxisDescription(name, label, values)
                axisDescriptions.append(axis)   

        return title, abstract, timepositions, timelimits, units, crss, axisDescriptions
            
    def getCoverageDescription(self):
        pass
        
      
    def map(self, **kwargs):
        """
        Given csml.parser.Dataset object list the names of
        all layers available.
        
        @return: A mapping of layer names to ILayer implementations.
        @raise ValueError: If no layers are available for these keywords. 
        """
        fileoruri=kwargs['fileoruri']
        if fileoruri in self.layermapcache.keys():
            #we've accessed this layer map before, get it from the cache dictionary
            return self.layermapcache[fileoruri]
        
        if self.connector.isGroup(fileoruri):
            self.datasetName = fileoruri
        else:
            
            ds = self.connector.getCsmlDoc(fileoruri)
            try:
                self.datasetName=ds.name.CONTENT
            except AttributeError:
                self.datasetName = 'CSML WCS Service'
            
            
        self._crscat=csml.csmllibs.csmlcrs.CRSCatalogue()
        
        if self.connector.isGroup(fileoruri):
            coverages = self._getCoveragesFromFolder(folderPath=fileoruri)
        else:
            coverages = self._getCoveragesFromCSMLFile(fileoruri)
        
        layermap = {}
        for c in coverages:
            layermap[c.name] = c
        
#        for feature in csml.csmllibs.csmlextra.listify(ds.featureCollection.featureMembers):
#            title, abstract, timepositions, timelimits, units, crss, axisDescriptions=self.getInfo(feature)
#            
#            name = feature.id
#            layermap[feature.id]=CSMLCoverage(name, [title],[abstract], 
#                                               timepositions, timelimits, units, 
#                                               crss, axisDescriptions, feature)
#            
        if len(layermap) > 0:
            self.layermapcache[fileoruri]=layermap
            return layermap 
        else:
            raise ValueError
    
    def _getCoveragesFromFolder(self, folderPath=None):
        l = []
        
        for fc in self.connector.list(folder=folderPath):
            
            if self.connector.isGroup(fc):
                l += self._getCoveragesFromFolder(folderPath=fc)
            else: 
                l += self._getCoveragesFromCSMLFile(fc)
                
        return l
    
    def _getCoveragesFromCSMLFile(self, fileoruri):
        l = []
        ds = self.connector.getCsmlDoc(fileoruri)
        
        for feature in csml.csmllibs.csmlextra.listify(ds.featureCollection.featureMembers):
            title, abstract, timepositions, timelimits, units, crss, axisDescriptions=self.getInfo(feature)
            
            name = fileoruri.replace('/','_') + '_' +feature.id
            c = CSMLCoverage(name, [title],[abstract], timepositions, timelimits, 
                             units,crss, axisDescriptions, feature)
            
            l.append(c)
    
        return l
                          
        
class AxisDescription(object):
    """ represents an axisDescription from the rangeSet (see wcs 1.0.0 describe coverage) """
    def __init__(self, name, label, values):
        self.name=name
        self.label=label
        self.values=values

class CSMLCoverage(object): #TODO: define ICoverage
    """ represents a WCS Coverage. Implements ICoverage """
    
    def __init__(self, name, title, abstract, timepositions, timelimits, units, crss, axisDescriptions, feature):
        self.name = name
        self.title=title
        self.abstract=abstract
        self.description='TO DO - coverage description'
        self.timePositions=timepositions
        self.timeLimits=timelimits
        self.units=units
        self.crss=crss
        self._feature=feature
        self.id=feature.id
        self.bboxes=[]
                
        csmlbb = self._feature.getCSMLBoundingBox()
        twoDCRS=csmlbb.get2DCRSName()
        #default to global bounding box:
        bb=[-180,90,180,90]
        if twoDCRS=='EPSG:4326':
            try:
                bb=csmlbb.getBox()
                #convert 0 - 360 to -180, 180 as per common WXS convention
                if abs(bb[2]-bb[0]) >= 359 and abs(bb[2]-bb[0]) < 361:
                    bb[0], bb[2]=-180, 180        
            except:
                #failed to get better bbox info from CSML file:
                pass
        self.wgs84BBox = WGS84BoundingBox(bb[:2],
                                         bb[2:])
        #now create list of all other bounding boxes:
        if twoDCRS not in ['EPSG:4326', None]:
            #then add this bbox to the list:
            alternativebbox=csmlbb.getBox()
            self.bboxes.append(BoundingBox([alternativebbox[0],alternativebbox[1]], [alternativebbox[2],alternativebbox[3]], twoDCRS))
        self.featureInfoFormats = ['text/html']
        self.axisDescriptions = axisDescriptions
    
    def getBBox(self, crs):
        """
        @return: A 4-typle of the bounding box in the given coordinate
            reference system.
        """
        #TODO: make this generic
        return self.wgs84BBox
    
    def getCvg(self, bbox, time=None, crs=None, response_crs=None, **kwargs):
        """
        Creates a subset of the layer in a particular CRS and set of
        dimensions.
        #TODO: this is all out of synch
        @param crs: The coordinate reference system.
        @param dimValues: A mapping of dimension names to dimension values
            as specified in the IDimension.extent
        @param renderOpts: A generic mapping object for passing rendering
            options
        @return: An object implementing ILayerSlab
        #create netcdf for whole lat/lon for given dimValues, use to init slab
        """

        log.debug('WCS: getSubset(%s, %s, %s)' % (bbox, time, crs))
        #unpack the Boundingbox.
        
        
        ############################# from old WCS stack #################
        boundingbox=bbox
        lon=self._feature.getLongitudeAxis()
        lat=self._feature.getLatitudeAxis()
        t=self._feature.getTimeAxis()
        if None in [lon, lat, t]:
            #TODO need to return a suitable wcs error.
            log.debug('warning, could not get correct axis info')
            #best guess!
            if t is None:
                t='time'
            if lon is None:
                lon = 'longitude'
            if lat is None:
                lat = 'latitude'
        
        #create selection dictionary:
        sel={}
        sel[lat]=(boundingbox[1], boundingbox[3])
        sel[lon]=(boundingbox[0], boundingbox[2])
        if time is not None:
            if  type(time) is unicode:
                sel[t]=str(time)
            else:
                sel[t]=time
                
        #z is the 4th axis/band (eg height or pressure or wavelength) requested via kwargs as defined in the rangeset.axisDescriptions.
        for kw in kwargs:
            log.debug(kw)
            log.debug(self._feature.getAxisLabels())
            for ax in self._feature.getAxisLabels():
                if ax not in [lat, lon, t]:
                    if ax == kw:
                        z=str(ax)
                        sel[z]=(kwargs[kw])
                        log.debug('Z axis: %s'%z)     
        ##################################################################
        log.debug('Final selection being made to the csml api %s'%str(sel))
        filename = extractToNetCDF(self._feature, sel)
        return filename
        
