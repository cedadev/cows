# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

"""
Abstract base classes for testing the interfaces defined in cows.service.*_iface

"""

import unittest
try:
    from PIL import Image
except ImportError:
    import Image

def assert_iterable(a):
    try:
        iter(a)
    except:
        raise AssertionError("Not Iterable")

class TestILayer(unittest.TestCase):
    """
    Abstract base class for testing ILayer implementations.  Set self.layer
    in subclasses.
    
    @cvar layer: An ILayer implementation to test.
    @note: Set self.__test__ to True to activate subclasses.
    
    """
    
    __test__ = False
    layer = NotImplementedError
    
    #!TODO: Put self.crss in wxs_iface.  
    #    (spascoe) I think self.crss was originally part of the
    #    ILayer when it was in wms_iface but appears to be missing from wxs_iface.
    #    If getBBox is part of ILayer we logically need to know which
    #    CRSs it supports.
    def test_attributes(self):
        assert self.layer.title != NotImplemented
        assert self.layer.abstract != NotImplemented
        if self.layer.featureInfoFormat != None:
            assert_iterable(self.layer.featureInfoFormat)

        assert_iterable(self.layer.crss)
 
    def test_getBBox(self):
        for crs in self.layer.crss:
            print 'Testing getBBox on CRS=%s' % crs
            bbox = self.layer.getBBox(crs)
            assert len(bbox) == 4
            try:
                [float(x) for x in bbox]
            except:
                raise AssertionError("BBox parameters not convertible to float")
            llx, lly, urx, ury = bbox
            assert llx < urx
            assert lly < ury
            
class TestIwmsLayer(TestILayer):
    def test_attributes(self):
        width, height = self.legendSize
        assert type(width) == int
        assert type(height) == int
        
    def test_dimensions(self):
        assert_iterable(self.layer.dimensions)
        for dimName, dim in self.layer.dimensions.items():
            assert dimName
            assert dim.units != NotImplemented
            assert_iterable(dim.extent)
            
    def test_getSlab(self):
        for crs in self.layer.crss:
            self.do_getSlab(crs)

    #-------------------------------------------------------------------------

    def do_getSlab(self, crs, renderOpts={}, extentIndex=0):
        dimVals = {}
        for dimName, dim in self.layer.dimensions.items():
            dimVals[dimName] = dim[extentIndex]

        slab = self.layer.getSlab(crs, dimVals, renderOpts)
        self.assert_isSlab(slab)
            
    def assert_isSlab(self, slab):
        attrs = ['layer', 'crs', 'dimValues', 'renderOpts', 'bbox']
        for attr in attrs:
            assert hasattr(slab, attr)
        
        img = slab.getImage(slab.bbox, 50, 50)
        assert isinstance(img, Image.Image)
        assert img.size == (50, 50)
        
    #!TODO: getLegendImage and getFeatureInfo.
        