# BSD Licence
# Copyright (c) 2009, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from csml2kml.Station import  WFSStationCollection
import math

class StationCollection(WFSStationCollection):
    def __init__(self, xml_stringorelem):
        super(StationCollection, self).__init__();
        if type(xml_stringorelem) is str:
            self.parseString(xml_stringorelem)
        else:
            self.parseXML(xml_stringorelem)
            
    def listAllLatLons(self):
        ''' returns a list of lat lon pairs [lat0, lon0, lat1, lon1, lat2, lon2,...latn, lonn] '''
        latlons=[]
        for station in self.stations:
            latlons.append(station.lat)
            latlons.append(station.lon)
        return latlons
        
    def getStationsInBBox(self, minlat, minlon, maxlat, maxlon):
        stationsInBbox = []
        for station in self.stations:
            if station.lat >= minlat:
                if station.lat <= maxlat:
                    if station.lon >= minlon:
                        if station.lon <= maxlon:
                            stationsInBbox.append(station)
        return stationsInBbox

    def getNearestStation(self,lat,lon):
        ''' Determines the station nearest to the given geospatial point in the station collection '''

        curNearest=None
        curDist = -1

        for station in self.stations:
                #calculate distance
                tempDist = self.getDist(lat, lon, station.lat, station.lon)
                #if distance is smaller than the current shortest distance
                if curDist < 0 or tempDist < curDist:
                        curNearest = station
                        curDist = tempDist
        return curNearest


    def getDist(self, srcLat, srcLon, destLat, destLon):
        '''Calculates the distance between to geospatial points'''      
        dlon = destLon - srcLon
        dlat = destLat - srcLat
        #a = (math.sin(dlat / 2))**2 + math.cos(srcLat) * math.cos(destLat) * (math.sin(dlon / 2))**2        
        #c = 2 * math.asin(min(1, math.sqrt(a)))
        #dist = 3956 * c
        dist = math.sqrt(dlat**2 + dlon**2)
        return dist
                
        
