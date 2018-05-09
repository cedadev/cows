# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""Routes configuration

The more specific and detailed routes should be defined first so they
may take precedent over the more generic routes. For more information
refer to the routes manual at http://routes.groovie.org/docs/
"""
from pylons import config
from routes import Mapper

def make_map():
    """Create, configure and return the routes Mapper"""
    map = Mapper(directory=config['pylons.paths']['controllers'],
                 always_scan=config['debug'])

    # The ErrorController route (handles 404/500 error pages); it should
    # likely stay at the top, ensuring it can always be resolved
    map.connect('error/:action/:id', controller='error')

    # CUSTOM ROUTES HERE
    map.connect(':fileoruri/wms', controller='csmlwms')
    map.connect('wcsroute', ':fileoruri/wcs', controller='csmlwcs') #wcsroute is a named route.
    map.connect(':fileoruri/wfs', controller='csmlwfs')
    #filestore - used for fetching files referenced by (csml) StorageDescriptors (WFS), and  'store' in wcs if implemented
    map.connect('filestore/:file', controller='fetch', action='fetchFile')
    map.connect(':fileoruri/demo', controller='demo')
    map.connect('', controller='catalogue')


    map.connect(':controller/:action/:id')
    map.connect('*url', controller='template', action='view')

    return map
