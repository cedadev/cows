# BSD Licence
# Copyright (c) 2010, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import logging

from cows.service.imps.csmlbackend.wcs_csmllayer import CSMLwcsCoverageMapper
from cows.pylons.wcs_controller import WCSController

log = logging.getLogger(__name__)

class CsmlwcsController(WCSController):
    layerMapper=CSMLwcsCoverageMapper()
