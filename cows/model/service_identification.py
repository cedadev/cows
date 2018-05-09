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
Classes modelling the OWS Service Identification package v1.1.0.

:author: Stephen Pascoe
"""

from cows.model.data_identification import Description

class ServiceIdentification(Description):
    """
    :ivar serviceType:
    :type serviceType: ows.iso19115_subset.Code
    :ivar serviceTypeVersions: The supported service versions
    :type serviceTypeVersions: iterable of str
    :ivar profiles:
    :type profiles: iterable of str
    :ivar fees: defaults to 'none'
    :type fees: str
    :ivar accessConstraints: defaults to 'none'
    :type accessConstraints: str

    """
    def __init__(self, serviceType, serviceTypeVersions=[],
                 profiles=[], fees="none", accessConstraints="none", **kwargs):
        """
        All parameters set default attributes of the instance.

        """
        super(self.__class__, self).__init__(**kwargs)
        self.serviceType = serviceType
        self.serviceTypeVersions = serviceTypeVersions
        self.profiles = profiles
        self.fees = fees
        self.accessConstraints = accessConstraints

