# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Base controller for OGC Web Services (OWS).

:author: Stephen Pascoe
:todo: Add pluggable security so replicate what was previously implemented
    for the NDG discovery portal in ows_server.lib.BaseController.
"""


from pylons import request, response, config, url
from pylons import tmpl_context as c
from pylons.controllers import WSGIController
from pylons.templating import render_genshi as render
from paste.util.multidict import MultiDict

from cows import exceptions as OWS_E
from cows.util import negotiate_version, check_updatesequence
from cows.builder import loadConfigFile
from cows import helpers
from cows.qs_util import parse_qsl
from cows.model import *

from genshi.template import TemplateLoader
from pkg_resources import resource_filename

try:
    from xml.etree import ElementTree as ET
except ImportError:
    from elementtree import ElementTree as ET

import logging
log = logging.getLogger(__name__)

# Instantiate Genshi template loader
templateLoader = TemplateLoader(
    resource_filename('cows.pylons', 'templates'),
    auto_reload=True,
    )

##########################################################################
# Configure
#

# Exception type should be 'ogc' for raising OGC exception XML or 'pylons'
#     to let pylons handle errors.
EXCEPTION_TYPE = config.get('cows.exception_type', 'ogc').lower()

# Parameter mode changes the way QUERY_STRING is parsed.  In 'html_4' mode
#     request.params is used, allowing the use of POST.  In 'wps_1' mode
#     QUERY_STRING is parsed directly to work arround an issue where WPS-1.0
#     treats ';' different to HTML4.
PARAMETER_MODE = config.get('cows.parameter_mode', 'html_4').lower()

##########################################################################

class OWSControllerBase(WSGIController):
    """
    Base class for all COWS Service controllers.  
    
    Subclasses should add supported operations to the cls.owsOperations attribute 
    and supply the a method of the same name (in UpperCammelCase).  
    
    When a request is received first self.__before__() will be called with the 
    parameters supplied by routes.  Override this method to configure the service 
    for a particular URL.  Then the operation method will be called
    with the same parameters as self.__before__().  The operation parameters 
    (query_string) are not sent as method arguments.  Use self.owsParams or 
    self.getOwsParam() to retrieve these parameters.
    
    :ivar owsParams: A dictionary of parameters passed to the service.
        Initially these comes from the query string but could come from
        a HTTP POST in future.
    :cvar owsOperations: A list of operation names

    The OWSControllerBase class supports requests via either HTTP "GET" or "POST".
    In keeping with the OGC specifications a POST request must provide a base URL
    and an XML request document. The query string will be ignored for a POST request.

    At various points this class tests which request method is being used in order
    to work out how to parse the request.   
    """

    owsOperations = []

    def __call__(self, environ, start_response):

        self._loadOwsParams()

        # If the EXCEPTION_TYPE is 'pylons' let Pylons catch any exceptions.
        # Otherwise send an OGC exception report for any OWS_E.OwsError
        if 'pylons' in EXCEPTION_TYPE:
#            start_response('200 OK', [('Content-type', 'text/plain')]); return ["HH"]
            self._fixOwsAction(environ)
            return super(OWSControllerBase, self).__call__(environ, start_response)
        else:
            try:
                self._fixOwsAction(environ)
                return super(OWSControllerBase, self).__call__(environ, start_response)

            except OWS_E.OwsError, e:
                log.exception(e)
                start_response('400 Bad Request', [('Content-type', 'text/xml')])
                return [render_ows_exception(e)]

            except Exception, e:
                log.exception(e)
                start_response('500 Internal Server Error', [('Content-type', 'text/plain')])
                return ['Please see server logs for details']

    def _loadOwsParams(self):
        """
        Method to load OWS parameters from the query string. 
        If request method is POST then this is ignored after creating
        the instance dictionary self._owsParams.
        """
        # All OWS parameter names are case insensitive.
        self._owsParams = {}

        if self._requestMethod() == "POST":
            return

        log.debug('REQUEST: %s' % request)
        
        if PARAMETER_MODE == 'html_4':
            params = request.params
        elif PARAMETER_MODE == 'wps_1':
            # request.params will use ';' as a QS separator which is not compatible
            # with WPS-1.0.  Therefore we parse the QS ourselves.
            qs = request.environ['QUERY_STRING']
            params = MultiDict(parse_qsl(qs, semicolon_separator=False,
                                         keep_blank_values=True, strict_parsing=False))
        else:
            raise ValueError("Value of cows.parameter_mode not recognised (%s)" % PARAMETER_MODE)

        #!TODO: unicode is converted here.
        # At some point we need to expect COWS apps to accept unicode
        try:
            for k in params:
                if k.lower() == 'x':
                    self._owsParams['i'] = str(params[k])
                elif k.lower() == 'y':
                    self._owsParams['j'] = str(params[k])
                else:
                    self._owsParams[k.lower()] = str(params[k])
        except UnicodeError:
            raise ValueError("Cannot convert unicode to string.  COWS does not accept unicode parameters")

    def _fixOwsAction(self, environ):
        rdict = environ['pylons.routes_dict']
        
        # Override the Routes action from the request query parameter
        # If request method is POST then need to look in top-level xml node to
        # get request action
        
        if self._requestMethod() == "POST":
            try:
                action = ET.fromstring(str(request.body)).tag.split("}")[-1]
            except:
                raise OWS_E.InvalidParameterValue("Unable to determine WPS Operation from XML Request received by POST method.")
        else:
            action = self.getOwsParam('request')

        # Check action is a method in self and is defined as an OWS operation
        if action not in self.owsOperations:
            raise OWS_E.InvalidParameterValue('request=%s not supported' % action,
                                              'REQUEST')
        rdict['action'] = action

    def _requestMethod(self):
        """
        Looks up pylons request object to determine request method.
        """
        return request.environ.get("REQUEST_METHOD")

    def getOwsParam(self, param, **kwargs):
        """
        Returns the value of a OWS parameter passed to the operation.
        If kwargs['default'] is given it is taken to be the default
        value otherwise the parameter is treated as mandatory and an
        exception is raised if the parameter is not present.

        """
        try:
            return self._owsParams[param.lower()]
        except KeyError:
            if 'default' in kwargs:
                return kwargs['default']
            else:
                raise OWS_E.MissingParameterValue('%s parameter is not specified' % param,
                                                  param)

#-----------------------------------------------------------------------------
# Functions that populate c.capabilities

def addOperation(opName, formats=[]):
    ops = c.capabilities.operationsMetadata.operationDict
    ops[opName] = helpers.operation(url.current(qualified=True, action="index")+'?', formats=formats)

def addLayer(name, title, abstract, srss, bbox, dimensions={}):
    """
    @param dimensions: Dictionary of dictionaries D[k1][k2]=val where
        k1 is dimension name, k2 is a keyword parameter to send to
        helpers.wms_dimension and val is it's value.

    :todo: The helpers interface is leaking through.  Could make cleaner.

    """
        
    if c.capabilities.contents is None:
        c.capabilities.contents = Contents()

    layer = helpers.wms_layer(name, title, srss, bbox, abstract)

    for k1, kwargs in dimensions.items():
        dim = helpers.wms_dimension(**kwargs)
        layer.dimensions[k1] = dim

    c.capabilities.contents.datasetSummaries.append(layer)

def initCapabilities():
    """
    Initialise the capabilities object c.capabilities.

    By default the server-wide configuration file is loaded and
    used to populate some standard metadata.  The GetCapabilites
    operation is added.

    """
    # Load the basic ServiceMetadata from a config file
    try:
        configFile = config['cows.capabilities_config']
    except KeyError:
        configFile = config.get('ows_server.capabilities_config')
    if configFile is None:
        raise RuntimeError('No OWS configuration file')
    
    c.capabilities = loadConfigFile(configFile)

    om = OperationsMetadata(operationDict={})
    c.capabilities.operationsMetadata = om

    addOperation('GetCapabilities', formats=['text/xml'])

#-----------------------------------------------------------------------------

class OWSController(OWSControllerBase):
    """
    Adds basic GetCapabilities response to OWSControllerBase.

    :cvar service: If None does not enforce the SERVICE parameter.  Otherwise
        raises exception if SERVICE is not correct on GetCapabilities request.
    :cvar validVersions: A list of supported version numbers.  Automatic
        version negotiation is performed according to this attribute.
    
    :ivar updateSequence: None if cache-control is not supported or an
        updateSequence identifier.  This attribute should be set in the
        controller's __before__() method.
    """

    owsOperations = ['GetCapabilities']

    # Override these attributes to control how OWSController responds to
    # GetCapabilities
    service = None
    validVersions = NotImplemented

    # To enable cache control set this instance attribute in self.__before__().
    updateSequence = None
    
    def GetCapabilities(self):
        """
        Main OWS operation is managed by this method.

        Depending on the request method being "GET" or "POST" it 
        gets its information from different places.

        """

        # Retrieve Operation parameters
        rm = self._requestMethod()
        if rm == "GET":
            ows_params = self._getGCParamsViaGET()
        elif rm == "POST": 
            ows_params = self._getGCParamsViaPOST()
        else:
            raise Exception("Request Method '%s' not supported." % rm)

        # Check update sequence
        check_updatesequence(self.updateSequence, ows_params["updateSequence"])

        # Do version negotiation
        version = negotiate_version(self.validVersions, ows_params["version"])

        # Get information required for the capabilities document
        initCapabilities()
        self._loadCapabilities()
        
        # Render the capabilities document        
        response.headers['content-type'] = ows_params["format"]
        return self._renderCapabilities(ows_params["version"], ows_params["format"])

    def _getGCParamsViaGET(self):
        """
        Method to support the self.GetCapabilities operation that
        used the GET method to obtain OWS parameters.
        """
        params = {}
        params["service"] = self.getOwsParam('service')
        params["version"] = self.getOwsParam('version', default=None)
        params["format"] = self.getOwsParam('format', default='text/xml')
        params["updateSequence"] = self.getOwsParam('updatesequence', default=None)         
        return params

    def _getGCParamsViaPOST(self):
        """
        Method to support the self.GetCapabilities operation that
        used the POST method to obtain OWS parameters.

        Not implemented in base class (OWSController) as child classes
        will have specific XML content from which to extract parameters.
        """
        pass

    def _loadCapabilities(self):
        """
        Override in subclasses to populate c.capabilities with
        operation and contents metadata.

        """
        pass

    def _renderCapabilities(self, version, format):
        """
        Override in subclasses to render the capabilities document.
        The response mime-type will already have been set.  Raise an
        OWS exception if the format is not supported.

        @param version: the version as a string
        @param format: the format as a string
        
        :return: a template as expected by pylons.render()
        """
        raise NotImplementedError


def render_ows_exception(e):
    tmpl = templateLoader.load('exception_report.xml')
    return str(tmpl.generate(report=e.report).render('xml'))


