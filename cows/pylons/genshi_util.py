# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Utilities for use with genshi

@author: Stephen Pascoe

"""

from genshi import *

class RenameElementFilter(object):
    """
    Rename the root element in the stream.

    Filters of this class will replicate the stream until the first START event
    then change the event element's QName.  It will then count opening and closing
    tags until it finds the matching close tag and replace the QName in that.  It
    then continues to replicate the stream.

    """

    def __init__(self, newQName):
        self.newQName = newQName
        # status 0: awaiting START, 1: awaiting END, 2: noop
        self.status = 0
        self.tcount = 0

    def __call__(self, stream):
        for kind, data, pos in stream:
            if self.status == 0:
                if kind == Stream.START:
                    self.status = 1
                    self.tcount = 1
                    yield kind, (self.newQName, data[1]), pos
                else:
                    yield kind, data, pos
            elif self.status == 1:
                if kind == Stream.START:
                    self.tcount += 1
                elif kind == Stream.END:
                    self.tcount -= 1

                if self.tcount == 0:
                    self.status == 2
                    yield kind, self.newQName, pos
                else:
                    yield kind, data, pos
            elif self.status == 2:
                yield kind, data, pos
