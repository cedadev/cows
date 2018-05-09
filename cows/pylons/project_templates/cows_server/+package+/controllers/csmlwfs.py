# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import logging

log = logging.getLogger(__name__)

from cows.service.imps.csmlbackend.wfs_csmllayer import CSMLwfsLayerMapper
from cows.pylons.wfs_controller import WFSController

class CsmlwfsController(WFSController):
        layerMapper=CSMLwfsLayerMapper()

