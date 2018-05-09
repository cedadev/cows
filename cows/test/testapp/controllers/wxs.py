# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import logging

log = logging.getLogger(__name__)

from pylons import response

from cows.pylons.ows_controller import OWSController, addOperation

class WxsController(OWSController):

    service = 'WXS'
    owsOperations = (OWSController.owsOperations + ['GetPiza'])

    validVersions = ['0.1']

    def _loadCapabilities(self):
        """This is a hook used to populate c.capabilites with service metadata.

        """
        pass

    def _renderCapabilities(self, version, format):
        """Select a Genshi template for rendering the capabilities according
        to version and format.

        c.capabilities will contain the OWS-Common model for the capabilities.

        Return any pylons controller response.
        """
        pass

    def GetPiza(self):
        toppings = self.getOwsParam('toppings',
                                    default='cheese,tomato').split(',')

        response.headers['Content-Type'] = 'text/plain'
        if len(toppings) > 1:
            t1 = toppings[:-1]
            t2 = toppings[-1]
            return 'One %s and %s piza to go!' % (', '.join(t1), t2)
        else:
            return 'One %s piza to go!' % toppings[0]
