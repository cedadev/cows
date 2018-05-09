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
Elementtree convenience utilities

@author: Stephen Pascoe

"""

def find_text(node, path):
    """Find a node's text or None

    """
    return getattr(node.find(path), 'text', None)

def findall_text(node, path):
    """Find all n.text elements from a path.

    """
    return [n.text for n in node.findall(path)]

def find_with(node, path, func):
    """If node.find(path) returns a node n return func(n) else return None.

    """
    n = node.find(path)
    if n is None:
        return None
    else:
        return func(n)

def findall_with(node, path, func):
    """Find all func(n) for n in node.findall(path).

    """
    return [func(n) for n in node.findall(path)]

