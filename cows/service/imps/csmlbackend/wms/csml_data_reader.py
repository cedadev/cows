# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.


import os

import csml
import cdms2 as cdms

from cows.service.imps.csmlbackend.config import config
from cows.service.imps.csmlbackend import getGlobalCSMLConnector

import numpy
import logging

log = logging.getLogger(__name__)
    
class CSMLDataReader(object):
    """
    Creates an object that can read cdms variable and other data from a csml 
    file.
    """
    
    def __init__(self, fileoruri):
        """
        Creates a data reader, the fileoruri provided indicates which csml file
        should be used.
        """

        self.connector = getGlobalCSMLConnector()
        self.fileoruri = fileoruri
        self.ds = self.connector.getCsmlDoc(fileoruri)
        self.varcache = {} 

    def getNetcdfVar(self, featureId,  dimValues):
        "Opens up the csml and retrieves the variable described by the dimensions"
        
        log.debug("featureId = %s, dimValues = %s" % (featureId, dimValues))
        
        dimList = list(dimValues.items())
        dimList.sort()
        
        cacheKey = "%s:%s" % (featureId, dimList)

        if cacheKey not in self.varcache:
        
            feature = self._getFeature(featureId)
            
            convertedDimVals = self._convertDimValues(dimValues)
            
            variable = None
            
            if type(feature) == csml.parser.GridSeriesFeature:
                
                randomname= csml.csmllibs.csmlextra.getRandomID() + '.nc'
                
                log.debug("getting csml feature tmpdir = %s, ncname = %s, convertedDimVals = %s" \
                          % (config['tmpdir'], randomname, convertedDimVals))
                
                result= feature.subsetToGridSeries(config['tmpdir'], 
                                            ncname=randomname, **convertedDimVals)
              
                extract = result[2]

                variable_name = extract.variableName.CONTENT
                
                #for now have to read netcdf back from 
                #disk (limitiation of CSML api)
                netcdf=cdms.open(result[1])
                try:                 
                    variable =  netcdf(variable_name, squeeze=1)
                finally:
                    netcdf.close()
                
                #and then delete the temporary file
                os.system('rm %s'%result[1])
                
                log.debug("removed temp file %s" % (result[1],))
                
            else:
                raise NotImplementedError
            
            
            #try to set any NAN variable to masked variables
            try:
                #replace any NaN's with masked values
                are_nan = numpy.isnan(variable)

                if are_nan.any():
                    # if the mask is just a single value we need to expand it
                    if variable.mask.shape != variable.shape:
                        
                        if variable.mask:
                            variable.mask = numpy.ones(variable.shape)
                        else:
                            variable.mask = numpy.zeros(variable.shape)
                        
                    variable[are_nan] = variable.getMissing()
                    variable.mask[are_nan] = True
            
            except:
                log.exception("Exception occurred while trying to fix NAN numbers in variable.")
                raise
            
            self.varcache[cacheKey] = variable
        else:
            variable = self.varcache[cacheKey]

        return variable
    

    def _getFeature(self, id):
        for feature in csml.csmllibs.csmlextra.listify(self.ds.featureCollection.featureMembers):
            if feature.id == id:
                return feature
            
        raise Exception("Feature with id %s not found" % (id,))

        
    def _convertDimValues(self, dimValues):
        """
        Converts the string dimension values to floats (except for time values)
        """
        convertedVals = {}
        
        for dimval in dimValues:
            if dimval != 'time':
                convertedVals[dimval]=float(dimValues[dimval])
            else:
                #remove any trailing Zs from time string
                if dimValues[dimval] [-1:] in ['Z', 'z']:
                    convertedVals[dimval]=dimValues[dimval][:-1]
                else:
                    convertedVals[dimval] = dimValues[dimval]  

        return convertedVals
    
    
    def getConfigAxisXMLFile(self):
        """
        Returns a path to the axis config XML file by reading it from the csml
        file.
        """
    
        xmlPath = None
        for m in self._getMetadataElements():
            
            if m.text is not None and len(m.text) > 0:
                metadataValue = m.text.strip()
                
                if metadataValue.find('AxisConfigXML') == 0:
                    xmlPath = metadataValue.split('=')[1]
        
        return xmlPath
    
    def _getMetadataElements(self):
        
        featureCollectionElt = None
        for c in self.ds.elem.getchildren(): 
            if c.tag.find('CSMLFeatureCollection') > -1:
                featureCollectionElt = c
                break
        
        metadataElements = []
        if featureCollectionElt != None:
            for c in featureCollectionElt.getchildren():
                if c.tag.find("metaDataProperty") > -1:
                    metadataElements.append(c)    

        return metadataElements
    