# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.


from cows.test.testapp.tests import TestController

class TestWXS(TestController):
    def testGetPiza(self):
        r = self.app.get('/wxs?REQUEST=GetPiza')
        assert 'One cheese and tomato piza to go!' in r.body

    def testException(self):
        r = self.app.get('/wxs?REQUEST=NoOp', status=400)
        assert r.status == 400
        assert 'ExceptionReport' in r.body
