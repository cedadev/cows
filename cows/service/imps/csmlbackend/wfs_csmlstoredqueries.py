# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

""" This module contains CSML WFS 2.0 stored query implementations. 
To add a new stored query, write the functional code here, then describe the functionality as 
a new query in:

wfs_csmllayer.CSMLStoredQueries.queries

These query functions should either return a resultset (python list) containing the features,
or 2 lists, one being the resultset, and the other containing string representations of XML addtional
objects - in CSML these are going to be StorageDescriptors.
"""
import wfs_csmllayer

import logging
log = logging.getLogger(__name__)
import csml.parser, csml.csmllibs.csmlextra
from xml.etree import ElementTree as etree
from pylons import request, config


class dummyfeaturefortesting(object):
    def __init__(self, x):
        self.x=x
    def toGML(self):
        return '<someGML>%s</someGML>'%self.x

def _getCSMLFilename():
    return 'csml%s.nc'%(csml.csmllibs.csmlextra.getRandomID())


def query_one_func(featureset, arg1='string1', arg2='string2'):
    result = [dummyfeaturefortesting(arg1 + ' ' + arg2)]
    return result

def query_getFeatureByPhenomenon(featureset, phenomenon):
    return featureset.getFeaturesByPropertyEqualTo('csml:parameter', phenomenon)    

def query_getFeatureById(featureset, id):
    return [featureset.getFeatureByGMLid(id)]

def query_extractPointFromPointSeries(featureset, featureid, timeinstance):
    #TODO:  configure output directory
    #TODO: error handling
    csmloutputdir=config['cows.csml.publish_dir']
    feature=featureset.getFeatureByGMLid(featureid)._feature
    ncname=_getCSMLFilename()
    newfeature, netcdfpath, storagedescriptor=feature.subsetToPoint(time=str(timeinstance), ncname=ncname, outputdir=csmloutputdir)        
    
    #modify the rangeset of the feature to store the data inline and discard the storage descriptor.
    storagedescriptor.fileName.CONTENT=csmloutputdir+'/'+storagedescriptor.fileName.CONTENT    
    data=storagedescriptor.getData()
    qlist=csml.parser.MeasureOrNullList()
    qlist.uom=newfeature.value.rangeSet.valueArray.valueComponent.uom
    qlist.CONTENT=str(data[0])
    rs=csml.parser.RangeSet()
    rs.quantityList=qlist    
    newfeature.value.rangeSet=rs
    
    #wrap the feature in a wfs CSMLFeatureInstance object:
    csmlfi=wfs_csmllayer.CSMLFeatureInstance('subset feature title', 'subset feature abstract', newfeature)
    return [csmlfi]
    #This following code is used to maintain the storage descriptor filename consistency, but has been commented out for this 
    #operation as there is only a single point value. However code is left here as reminder as it will be needed 
    #for other feature types soon
    #change the path of the storage descriptor to the download url - assumes routes maps to filestore
    
    #And serialise the storage descriptor as XML.
#    qualifiedFeatureType='{http://ndg.nerc.ac.uk/csml}' + storagedescriptor.__class__.__name__ 
#    emptyelem=etree.Element(qualifiedFeatureType)
#    log.debug(request.environ)    
#    storagedescriptor.fileName.CONTENT='http://'+request.environ['HTTP_HOST']+'/filestore/' +storagedescriptor.fileName.CONTENT
#    csmlelem=storagedescriptor.toXML(emptyelem)
#    storagedescXML=etree.tostring(csmlelem)      
#    return [csmlfi], [storagedescXML]

def query_extractPointSeriesFromPointSeries(featureset, featureid, starttime, endtime):
    csmloutputdir=config['cows.csml.publish_dir']
    feature=featureset.getFeatureByGMLid(featureid)._feature
    timerange=(starttime, endtime,)
    subsetdictionary={'times':timerange}
    ncname=_getCSMLFilename()
    newfeature, netcdfpath, storagedescriptor=feature.subsetToPointSeries(outputdir=csmloutputdir, ncname=ncname,**subsetdictionary)
    #wrap this in a wfs CSMLFeatureInstance object:
    csmlfi=wfs_csmllayer.CSMLFeatureInstance('subset feature title', 'subset feature abstract', newfeature)
    #And serialise the storage descriptor as XML.
    qualifiedFeatureType='{http://ndg.nerc.ac.uk/csml}' + storagedescriptor.__class__.__name__ 
    emptyelem=etree.Element(qualifiedFeatureType)
    log.debug(request.environ)
    #change the path of the storage descriptor to the download url - assumes routes maps to filestore
    #TODO: THIS SHOULD HANDLE SERVER PROXIES.
    storagedescriptor.fileName.CONTENT='http://'+request.environ['HTTP_HOST']+'/filestore/' +ncname
    csmlelem=storagedescriptor.toXML(emptyelem)
    storagedescXML=etree.tostring(csmlelem)
    return [csmlfi], [storagedescXML]


def query_extractPointSeriesFromGridSeries(featureset, featureid, latitude, longitude, mintime, maxtime):
    csmloutputdir=config['cows.csml.publish_dir']
    feature=featureset.getFeatureByGMLid(featureid)._feature
    timerange=(mintime, maxtime,)
    lat=float(latitude)
    lon=float(longitude)
    subsetdictionary={'time':timerange, 'latitude':lat, 'longitude':lon}
    ncname=_getCSMLFilename()
    newfeature, netcdfpath, storagedescriptor=feature.subsetToPointSeries(outputdir=csmloutputdir, ncname=ncname,**subsetdictionary)
    #wrap this in a wfs CSMLFeatureInstance object:
    csmlfi=wfs_csmllayer.CSMLFeatureInstance('subset feature title', 'subset feature abstract', newfeature)
    #And serialise the storage descriptor as XML.
    qualifiedFeatureType='{http://ndg.nerc.ac.uk/csml}' + storagedescriptor.__class__.__name__ 
    emptyelem=etree.Element(qualifiedFeatureType)
    log.debug(request.environ)
    #change the path of the storage descriptor to the download url - assumes routes maps to filestore
    #TODO: THIS SHOULD HANDLE SERVER PROXIES.
    storagedescriptor.fileName.CONTENT='http://'+request.environ['HTTP_HOST']+'/filestore/' +ncname
    csmlelem=storagedescriptor.toXML(emptyelem)
    storagedescXML=etree.tostring(csmlelem)
    return [csmlfi], [storagedescXML]
 

def query_extractGridSeriesFromGridSeries(featureset, featureid, bbox, mintime, maxtime):
    #TODO factor out code in common with other subsetting queries
    csmloutputdir=config['cows.csml.publish_dir']
    feature=featureset.getFeatureByGMLid(featureid)._feature
    timerange=(mintime, maxtime,)
    #break the bounding box into latitude and longitude: 
    #TODO, this really needs to be generic and refer to the srs of the underlying feature.
    bb=str(bbox).split(',')
    lat=(float(bb[1]),float(bb[3]))
    lon=(float(bb[0]),float(bb[2]))
    log.debug('requesting latitude: %s, longitude: %s'%(lat, lon))
    ncname=_getCSMLFilename()
    newfeature, netcdfpath, storagedescriptor=feature.subsetToGridSeries(time=timerange, latitude=lat, longitude=lon, ncname=ncname, outputdir=csmloutputdir)
    #wrap this in a wfs CSMLFeatureInstance object:
    csmlfi=wfs_csmllayer.CSMLFeatureInstance('subset feature title', 'subset feature abstract', newfeature)
    #And serialise the storage descriptor as XML.
    qualifiedFeatureType='{http://ndg.nerc.ac.uk/csml}' + storagedescriptor.__class__.__name__ 
    emptyelem=etree.Element(qualifiedFeatureType)
    log.debug(request.environ)
    #change the path of the storage descriptor to the download url - assumes routes maps to filestore
    storagedescriptor.fileName.CONTENT='http://'+request.environ['HTTP_HOST']+'/filestore/' +storagedescriptor.fileName.CONTENT
    csmlelem=storagedescriptor.toXML(emptyelem)
    storagedescXML=etree.tostring(csmlelem)
    return [csmlfi], [storagedescXML]
    