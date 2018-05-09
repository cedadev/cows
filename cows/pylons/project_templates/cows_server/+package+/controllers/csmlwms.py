# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import logging

from cows.pylons.wms_controller import WMSController
#from cows.service.imps.csmlbackend.wms_csmllayer import CSMLwmsLayerMapper
from cows.service.imps.csml_geoplot_backend.csml_geoplot_layer_mapper import CSMLGeoplotLayerMapper


log = logging.getLogger(__name__)

class CsmlwmsController(WMSController):
#    layerMapper = CSMLwmsLayerMapper()
    layerMapper = CSMLGeoplotLayerMapper()


