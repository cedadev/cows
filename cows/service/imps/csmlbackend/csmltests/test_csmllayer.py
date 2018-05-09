# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

import cows.service.imps.csmlbackend.wms_csmllayer
import csml

#TODO: This test is out of date, needs updating and moving to cows.tests 

def test_layerMapper():
    lm=wms_csmllayer.CSMLwmsLayerMapper()
    print 'building layermap'
    file='hadgem1'
    layers=lm.map(fileoruri=file)
    
    #for key, layer in layers.items():
        #print '*********************'
        #print 'name: %s'%key  #name is currently gml:id..
        #print 'title: %s'%layer.title
        #print 'abstract: %s'%layer.abstract
        #print 'dimensions: %s'%layer.dimensions
        #for dim in layer.dimensions:
            #print layer.dimensions[dim].units
            #print layer.dimensions[dim].extent
        #print 'units: %s'%layer.units
        #print 'crss: %s'%layer.crss
        #print '*********************'
        
    #should be 35 features in this file
    layerid='UkndO02d'
    assert len(layers) == 35
    assert layers[layerid].title == 'm1s3i223'
    assert layers[layerid].abstract=='SURF & BL TOTL MOISTURE FLUX KG/M2/S'
    assert layers[layerid].units == ['degrees_east', 'degrees_north', 'none', 'days_since_1970-01-01_00:00:0']
    assert layers[layerid].crss == ['EPSG:4326']
    assert layers[layerid].dimensions.keys() == ['latitude', 'z0_surface', 'longitude', 'time']
    #layerid='EAY38o0Z'   #total precip
    layerid='DiXD05pN' #solar_1
    print 'getting slab...'
    slab= layers[layerid].getSlab('EPSG:4324', dimValues={'time':'1999-12-06T12:00:00.0', 'z0_surface':'0'})
    img=slab.getImage((-80, -160, 80, 160) ,320, 320)
    img.save("testimage.jpeg", "JPEG")
    print 'getting slab2...'
    slab2= layers[layerid].getSlab('EPSG:4324', dimValues={'time':'1998-12-06T12:00:00.0', 'z0_surface':'0'})
    img2=slab2.getImage((-80, -160, 80, 160) ,320, 320)
    img2.save("testimage2.jpeg", "JPEG")
    
    #Temperature:
    print 'getting slab3...'
    layerid = 'RJ1QcBwz'
    slab3= layers[layerid].getSlab('EPSG:4324', dimValues={'time':'1995-12-06T12:00:00.0', 'height':'0'})
    img3=slab3.getImage((-80, -160, 80, 160) ,320, 320)
    img3.save("testimage3.jpeg", "JPEG")
    
    print 'getting lots of images'
    miny=-90
    minx=-180
    maxy=90
    maxx=180
    for i in range(8):
        miny=miny+10
        minx=minx+10
        maxy=maxy -10
        maxx=maxx-10
        img=slab3.getImage((miny, minx, maxy, maxy) ,320, 320)
        img.save("sequence%s.jpeg"%str(i), "JPEG")
    
    
    
    
    
def main():
    test_layerMapper()
    
if __name__=="__main__":
    main()
