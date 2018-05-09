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
Utilities for OWS protocol processing.

@author: Stephen Pascoe
"""

from cows import exceptions as OWS_E


def parse_version(version):
    """
    Convert a version string into a tuple of integers suitable for doing
    comparisons on.

    """
    return tuple(int(x) for x in version.split('.'))

def serialise_version(version):
    """
    Convert a version tuple back to a string.

    """
    return '.'.join(str(v) for v in version)

def negotiate_version(serverVersions, clientVersion=None):
    """
    Negotiate which OWS version to use based on the version supplied by
    the client and the list of supported versions.

    """
    versions = [parse_version(v) for v in serverVersions]
    versions.sort()
    
    if clientVersion is None:
        return serialise_version(versions[-1])
    
    cv = parse_version(clientVersion)

    pv = versions[0]
    for v in versions:
        if cv == v:
            return serialise_version(v)
        if cv < v:
            return serialise_version(pv)
        pv = v

    return serialise_version(pv)


def check_updatesequence(clientUpdateSequence, serverUpdateSequence):
    if clientUpdateSequence and serverUpdateSequence:
        if client_updatesequence == serverUpdateSequence:
            raise OWS_E.CurrentUpdateSequence
        elif client_updatesequence > serverUpdateSequence:
            raise OWS_E.InvalidUpdateSequence
    
                     

#-----------------------------------------------------------------------------

_test_versions = ['1.0', '1.1.1', '1.3.0']
def test_version_negotiation1():
    assert negotiate_version(_test_versions) == (1, 3, 0)
def test_version_negotiation2():
    assert negotiate_version(_test_versions, '0.1') == (1, 0)
def test_version_negotiation3():
    assert negotiate_version(_test_versions, '1.4') == (1,3,0)
def test_version_negotiation4():
    assert negotiate_version(_test_versions, '1.1.1') == (1,1,1)
def test_version_negotiation5():
    assert negotiate_version(_test_versions, '1.2') == (1,1,1)

