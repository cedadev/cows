# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

'''A test/demo for classes contained in the Station.py module.'''

from csml2kml.Station import NPStation, WFSStationCollection
from csml2kml.utils import wget
from csml2kml.StationCollection import StationCollection

# Get XML response from a GeoServer via HTTP (should return several features
geoServerUrl ='http://bond.badc.rl.ac.uk:8084/geoserver/wfs?request=getfeature&service=wfs&version=1.1.0&typename=np:Station&maxfeatures=14'
geoServerResponse = wget(geoServerUrl)


# Create a WFSStationCollection object, which is a representation of a <wfs:StationCollection> XML element.
stationCollection=StationCollection(geoServerResponse)

# Each station is a NPStation object, which is a representation of a <np:Station> XML element.
for station in stationCollection.stations:
    print str(station)
    print station.lat
    print station.lon
    
print stationCollection.listAllLatLons()
for station in stationCollection.getStationsInBBox(60.43, -10, 60.58, 10):
    print 'Station: %s, %s'%(station.id, station.desc)

