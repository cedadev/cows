# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

# Copyright (C) 2007 STFC & NERC (Science and Technology Facilities Council).
# This software may be distributed under the terms of the
# Q Public License, version 1.0 or later.
# http://ndg.nerc.ac.uk/public_docs/QPublic_license.txt
"""
Classes modelling the OWS Operations Metadata package v1.1.0.

This module makes several simplifications to the OWS model to make it
more pythonic and restrict the model to it's common usage.

 1. Each operation can have 0..1 get and post request methods
 2. DCP's are not modelled.  Only HTTP DCP is supported.
 3. Operation.name becomes a key in the OperationsMetadata.operationDict
    attribute.

:author: Stephen Pascoe
"""

from cows.model.iso19115_subset import OnlineResource

class OperationsMetadata(object):
    """
    :note: extendedCapabilities could be implemented by subclassing.

    :ivar operationDict:
    :type operationDict: dictionary mapping names to Operation objects
    :ivar constraints:
    :type constraints: dictionary of Domain objects
    :ivar parameters:
    :ivar parameters: dictionary of Domain objects

    """
    def __init__(self, operationDict, constraints={}, parameters={}):
        self.operationDict = operationDict
        self.constraints = constraints
        self.parameters = parameters

    @classmethod
    def fromOperations(klass, **kwargs):
        """A convenient factory class method for operations.

        @param kwargs: A mapping of operation name to Operation objects

        """
        return klass(operationDict=kwargs)

class Operation(object):
    """
    :note: This class encompasses Operation, DCP and HTTP classes from OWS.
    
    :ivar get:
    :type get: None or RequestMethod
    :ivar post:
    :type post: None or RequestMethod
    :ivar constraints:
    :type constraints: dictionary of Domain objects
    :ivar parameters:
    :type parameters: dictionary of Domain objects
    :ivar name:
    :type name: None or str

    :todo: Do we need name now?  It duplicates OperationsMetadata.operationDict keys.
    
    """
    def __init__(self, get=None, post=None, constraints={}, parameters={}, name=None):
        self.get = get
        self.post = post
        self.constraints = constraints
        self.parameters = parameters
        self.name=name

class RequestMethod(OnlineResource):
    """
    :ivar constraints:
    :type constraints: dictionary of Domain objects

    """
    def __init__(self, constraints={}, **kwargs):
        super(RequestMethod, self).__init__(**kwargs)

        self.constraints = constraints

    
