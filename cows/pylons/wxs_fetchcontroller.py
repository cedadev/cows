# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import os, logging
from pylons.controllers import WSGIController
from pylons import request, response, config, session
from pylons import tmpl_context as c

log=logging.getLogger(__name__)
class WXSFetchController(WSGIController):
    ''' returns a file from the filestore. Used for the WCS store parameter in WCS 1.1.0, and also used for 
    fetching of documents referenced by CSML storagedescriptors in the WFS. Could also be used for other services.
    checks the security information in the text file that accompanies the file and checks ndg security - TODO, this will need 
    revising when we have new security integration'''
    def _getMimeType(self, file):
        if os.path.splitext(file)[1]=='.nc':
            return 'application/cf-netcdf'
        else:
            return 'application/unknown'
        
        
    def fetchFile(self, file):
        logging.info("Fetching file, '%s'" %file)
        
        #given the filename, these are the paths to the file, and to the accompanying text file
        filePath=config['cows.csml.publish_dir'] + '/' + file
        
        #just return the file, no security check implemented for now.
        fileToReturn=open(filePath, 'r')
        mType=self._getMimeType(file)
        response.headers['Content-Type']=mType
        return response.write(fileToReturn.read())
        
        #textFilePath=config['publish_dir'] +'/'+os.path.splitext(os.path.basename(file))[0]+'.txt'

#        This is all to handle ndg security, which isn't implemented here. Leaving the code here for now for future reference.
#        #open the text file and read security credentials
#        input =open(textFilePath, 'r')
#        sec=input.read()
#        log.debug('This is the security information in the text file: %s'%len(sec))
#        #check current users credentials
#        #if they match, return the file
#        #TODO, check this properly
#        if sec=='No Security':
#            match=True #allow 
#            log.debug('There is no security on this file')      
#        elif 'ndgSec' in session:
#            #if username matches
#            if sec == str(session['ndgSec']['u']):
#                match=True #allow         
#            else:
#                match=False #deny
#        else:
#             match=False  #deny      
#        if match:
#            #return the file (netcdf)
#            fileToReturn=open(filePath, 'r')
#            mType=self._getMimeType(file)
#                      
#            response.headers['Content-Type']=mType
#            return response.write(fileToReturn.read())
#        else:
#            #return access denied message
#            c.xml='<div class="error">%s</div>'%'<p> Access Denied </p><p>Not Logged in</p>'
#            return render('error')
