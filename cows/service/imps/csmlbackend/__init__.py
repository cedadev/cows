# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.



_globalCSMLConnector = None

def getGlobalCSMLConnector():
    global _globalCSMLConnector
    
    if _globalCSMLConnector is None:
        from cows.service.imps.csmlbackend.csmlcommon import CSMLConnector
        _globalCSMLConnector = CSMLConnector()
    
    return _globalCSMLConnector