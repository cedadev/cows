# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Test that the testapp Pylons application is correctly initialised.

"""

from cows.test.testapp.tests import TestController

class TestFixture(TestController):
    def testStaticPage(self):
        r = self.app.get('/test.html')
        assert 'TEST COWS testapp' in r.body

