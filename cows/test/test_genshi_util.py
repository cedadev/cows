# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Test functions that work with genshi templates.

@author: Stephen Pascoe

"""

from cows.pylons.genshi_util import RenameElementFilter
from genshi import XML, QName

def test_renameElement():
    """
    Check that renameElementFilter renames the root element of a stream.

    """
    xmlStream = XML('''<foo xmlns="http://example.com" flub="2"><bar baz="1">fofof</bar></foo>''')

    f = RenameElementFilter(QName('waze'))

    xml = (xmlStream | f).render()

    print xml

    assert xml == '<waze xmlns="http://example.com" flub="2"><bar baz="1">fofof</bar></waze>'
