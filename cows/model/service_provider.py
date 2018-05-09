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
Classes modelling the OWS Service Provider package v1.1.0.

:author: Dominic Lowe

"""

class ServiceProvider(object):
    """
    :ivar providerName:
    :type providerName: None or str
    :ivar serviceContact:
    :type serviceContact: None or ResponsibleParty
    :ivar providerSite:
    :type providerSite: None or OnlineResource
    """
    def __init__(self, providerName, serviceContact=None, providerSite=None):
        self.providerName=providerName
        self.serviceContact=serviceContact
        self.providerSite=providerSite

