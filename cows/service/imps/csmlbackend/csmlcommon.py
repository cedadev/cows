# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

""" Common CSML code shared between WMS, WFS and WCS backends 
@Author: Dominic Lowe 
"""

import os, string
import logging
import csml
import tempfile

from cows.service.imps.csmlbackend.config import config
from cows.service.imps.csmlbackend import getGlobalCSMLConnector

import ConfigParser
log = logging.getLogger(__name__)
from cows.bbox_util import union
 
try:
    from ndgUtils import ndgObject, ndgRetrieve
except:
    log.warning("ndgUtils library could not be loaded, files in the eXist database won't be available, although you should still be able to access files from the csmlstore directory referenced in the ini file.")

from cows.service.wxs_iface import ILayerMapper

try: #for python 2.5
    from xml.etree import ElementTree as ET
except ImportError:
    try:
        # if you've installed it yourself it comes this way
        import ElementTree as ET
    except ImportError:
        # if you've egged it this is the way it comes
        from elementtree import ElementTree as ET






def extractToNetCDF(feature, sel, publish=False):
    """
       performs the CSML subset and returns a filename of the netcdf extract
       publish flag is used to indicate that the netcdf file should be made available to the webserver (for asynchronous delivery)
    """

    if publish:
        #if publishing to download directory is required, do so and return publishable file name
        #used e.g. in WCS when "STORE = true"
        extract_dir=config['publish_dir']
    else:
        extract_dir = config['tmpdir']
         
    # Subset the feature
    (fd, filename) = tempfile.mkstemp('.nc', 'csml_wxs_', extract_dir); os.close(fd)
    if type(feature) is csml.parser.GridSeriesFeature:
        feature.subsetToGridSeries(ncname=os.path.basename(filename), outputdir=os.path.dirname(filename) ,**sel)
    elif type(feature) is csml.parser.TrajectoryFeature:
        feature.subsetToTrajectory(ncname=os.path.basename(filename), outputdir=os.path.dirname(filename) ,**sel)
    elif type(feature) is csml.parser.PointSeriesFeature:
        del sel['longitude'] #delete dummy values
        del sel['latitude'] #delete dummy values
        feature.subsetToPointSeries(ncname=os.path.basename(filename), outputdir=os.path.dirname(filename) ,**sel)
    elif type(feature) is csml.parser.RaggedSectionFeature:
        del sel['longitude'] #delete dummy values
        del sel['latitude'] #delete dummy values
        feature.subsetByTime(ncname=os.path.basename(filename), outputdir=os.path.dirname(filename) ,**sel)
    return filename


class CSMLLayerMapper(ILayerMapper):
    """
    Map keyword arguments to a collection of layers.
    Supports the retrieval of sets of layers according to arbitrary
    keyword/value pairs.
    Implements  ILayerMapper 
    
    """
    def __init__(self):
        self.layermapcache={}
        self.connector = getGlobalCSMLConnector()
    
    #!TODO: Should be _getInfo() as proposed in wms_csmllayer.  Should move to wfs_csmllayer as
    #    this is the only place where it isn't overridden.
    def getInfo(self, feature):
        ''' given a csml feature, return basic info about the layer/feature/coverage
        @return:   title, abstract'''

        try:
            title=feature.name.CONTENT
        except:
            title=''
        try:
            abstract=feature.description.CONTENT
        except:
            abstract=title
        
        return title, abstract

class CSMLConnector(object):
    """ Contains common methods for CSML backend used across all WXS services """    
    
    def __init__(self):
        self.csml_dir = config.get('csmlstore')
    
    def _locateFile(self, fileoruri):
        ''' gets the csml file from Exist or the csml filestore''' 
        if string.find(fileoruri,'__NDG-A0__') == -1:
            #it's a local file not an identifier, read from local csmlstore
            file=fileoruri
            path = os.path.join(self.csml_dir, file)
            if os.path.exists(path+'.csml'):
                f = path+'.csml'
            elif os.path.exists(path+'.xml'):
                f = path +'.xml'
            else:
                raise ValueError("Cannot find CSML file %s" % file)        
        else:
            #it's an NDG identifier, get the document from exist.
            uri=fileoruri 
            uriN=ndgObject(uri)
            conflocation=config['ndgconfig']
            cf=ConfigParser.ConfigParser()
            cf.read(conflocation)
            status,f=ndgRetrieve(uriN, cf, discovery=0)
        return f
    
    def getCSMLDatasetInfo(self,fileoruri):
        """ lightweight method that gets a CSML document, but only returns certain attributes that can easily be extracted using xpath
        This allows you to quickly get some key metadata without parsing the whole document.
        Returns a dictionary of attribute:value pairs. First version only returns dataset name"""
        datasetInfo={}
        f=self._locateFile(fileoruri)
        tree=ET.parse(f) #parse usign cElementTree
        nameelem=tree.find('{http://ndg.nerc.ac.uk/csml}name')
        #skip if name is not there or has one of the default entries
        if nameelem is not None:
            if nameelem.text in ['NAME OF DATASET GOES HERE', 'Please add a human readable name for the dataset here']:
                pass
            else:
                datasetInfo['name']=nameelem.text
        return datasetInfo
    
    def getCsmlDoc(self, fileoruri):
        """
        Gets a csml document from file or exist when passed a file name or uri

        Note, access control is not implemented on file access, only on exist
        access.
        
        """
        f=self._locateFile(fileoruri)
        d=csml.parser.Dataset()
        d.parse(f)                      
        return d
    
    def getColourMapConfig(self, fileoruri):
        """ looks for a mydataset.ini file alongside the csml mydataset.xml file
        the config file contains entries for max min values of data e.g. for use in consistent colourmapping """
        configfile=None
        file=fileoruri
        
        path = os.path.join(self.csml_dir, file)
        if os.path.exists(path+'.ini'):
            f = path+'.ini'
            configfile=ConfigParser.ConfigParser()
            configfile.read(f)              
        return configfile
  
        
        

    
    def list(self, folder=None):
        """
        Generator that lists available CSML documents.

        @note: not implemented for eXist.  I'm not sure if this is possible
            or desireable.

        """
        if self.csml_dir is None:
            log.warning('Trying to list CSMLConnector with no filestore.  '
                        'Maybe using eXist?')
            return
        
        path = self.csml_dir
        
        if folder != None:
            path = os.path.join(path, folder)
        
        for fp in os.listdir(path):
            
            if os.path.isdir(os.path.join(path,fp)):
                if folder != None:
                    # return 'folder/folder'
                    yield os.path.join(folder, fp)
                else:
                    # return 'folder'
                    yield fp
                
            if os.path.splitext(fp)[1] in ['.csml', '.xml']:
                if folder != None:
                    # return 'folder/file' without the .csml
                    yield os.path.join(folder, os.path.splitext(fp)[0])
                else:
                    # return 'file' without the .csml
                    yield os.path.splitext(fp)[0]
        
#        for dirpath, dirnames, filenames in os.walk(self.csml_dir):
#            for filename in filenames:
#                file_id, ext = os.path.splitext(filename)
#                if ext in ('.xml', '.csml'):
#                    # Remove common path bit
#                    relpath = dirpath[len(self.csml_dir):]
#                    
#                    if len(relpath) > 0 and relpath[0] == '/':
#                        relpath = relpath[1:]
#                    
#                    yield os.path.join(relpath, file_id)
                    
    def listwfsonly(self):
            """
        Generator that lists all CSML endpoints that can't be served through WMS/WCS.
        This list is (optionally)   defined in the wfsonly.txt file in the csml directory.
            """
            cfgfile = os.path.join(self.csml_dir, 'wfsonly.txt')
            if os.path.exists(cfgfile):
                f=open(cfgfile, 'r')
                for line in f:
                    yield line.strip('\n')
                f.close()
            else:
                return
    
    def isGroup(self, fc):
        return os.path.isdir(os.path.join(self.csml_dir, fc))

