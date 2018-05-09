# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Utility functions for running tests.
"""

import os

from csml import csmlscan

data_dir = os.path.abspath(os.path.dirname(__file__)) + '/data'

def init_csml(csml_id):
    """
    Run csmlcsan on the test data.

    @param csml_id: Name of file in test/data/csml without the .xml suffix.
    
    """

    # Write the config file with full pathnames
    cfg_path = os.path.join(data_dir, 'csml.cfg')
    fh = open(cfg_path, 'w')
    fh.write("""
[dataset]
dsID:%(id)s

[features]
type: GridSeries
number: many

[files]
root: %(here)s/csml
mapping: onetomany
output: %(here)s/csml/%(id)s.xml
printscreen:0

[spatialaxes]
spatialstorage:fileextract

[values]
valuestorage:fileextract

[time]
timedimension: t
timestorage:inline
""" % dict(here=data_dir, id=csml_id))
    fh.close()

    # Run csmlscan
    csmlscan.main(['csmlscan', '-c', cfg_path])

def make_data():
    init_csml('test_01')
