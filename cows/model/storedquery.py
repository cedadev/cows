# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""WFS 2.0 StoredQuery, ParameterExpression and QueryExpressionText classes
@author: Dominic Lowe (BADC)"""

class StoredQuery(object):
    def __init__(self, id, title=None, abstract=None,metadata=None, parameter=[], queryExpressionText=None ):
        self.id=id
        self.title=title
        self.abstract=abstract
        self.metadata=metadata
        self.parameter=parameter
        self.queryExpressionText=queryExpressionText
    
class ParameterExpression(object):
    def __init__(self, name, type, title=None, abstract=None, metadata=None):
        self.name=name
        self.type=type
        self.title=title
        self.abstract=abstract
        self.metadata=metadata
    
class QueryExpressionText(object):
    def __init__(self, returnFeatureType, language='urn-x:wfs:StoredQueryLanguage:WFS_QueryExpression', any=None, isPrivate=True):
        self.returnFeatureType=returnFeatureType        
        self.language=language
        self.any=any
        self.isPrivate=isPrivate
    
    