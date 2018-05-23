
"""
BSD 3-Clause License

Copyright (c) 2018, IMT Atlantique
All rights reserved.

This file is part of vastplace

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
  list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
  this list of conditions and the following disclaimer in the documentation
  and/or other materials provided with the distribution.

* Neither the name of the copyright holder nor the names of its
  contributors may be used to endorse or promote products derived from
  this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

@author Tanguy Kerdoncuff
"""
from bs4 import BeautifulSoup
import math
import pycurl
from StringIO import StringIO
from gridfs import GridFS
from bson.objectid import ObjectId

from centraldb.decorators import cached_call
from storage import database

CIRC_EARTH = 40075000
RADIUS_EARTH = 6367000

def meterDist( u, v):
	lat1, lon1, lat2, lon2 = map(math.radians, [u[0], u[1], v[0], v[1]])

	dlon = lon2 - lon1
	dlat = lat2 - lat1

	a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
	dist = RADIUS_EARTH * 2 * math.asin(math.sqrt(a))

	return dist

def point_projection_on_line(p, seg, testSegmentEnds=False):
	"""
	Planar Projection of a point on a line
        testSegmentEnds limits the projection to the segment, if False, the whole line is used
	"""

	x3,y3 = p
	(x1,y1),(x2,y2) = seg

	dx21 = (x2-x1)
	dy21 = (y2-y1)

	lensq21 = dx21*dx21 + dy21*dy21
        #Check for degenerate segment
	if lensq21 == 0:
	    return (x1, y1)

	u = (x3-x1)*dx21 + (y3-y1)*dy21
	u = u / float(lensq21)

	x = x1+ u * dx21
	y = y1+ u * dy21

	if testSegmentEnds:
	    if u < 0:
	        x,y = x1,y1
	    elif u >1:
	        x,y = x2,y2

	return (x,y)

def point_distance_to_line(p, seg, testSegmentEnds=False):
	"""
	Distance in meters of a point to a line
        testSegmentEnds limits the projection to the segment, if False, the whole line is used
	"""
        projection = point_projection_on_line(p, seg, testSegmentEnds)
        return meterDist(p, projection)



#Openstreetmap tile number to lat/lon converters
def osm_latlon_to_tile_number(lat_deg, lon_deg, zoom):
	""" returns the tile numbers depending on the latitude, longitude and zoom level of a point"""
	lat_rad = math.radians(lat_deg)
	n = 2.0 ** zoom
	xtile = int((lon_deg + 180.0) / 360.0 * n)
	ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
	return (xtile, ytile)

def osm_tile_number_to_latlon(xtile, ytile, zoom):
	""" Returns the latitude and longitude of the north west corner of a tile, based on the tile numbers and the zoom level"""
	n = 2.0 ** zoom
	lon_deg = xtile / n * 360.0 - 180.0
	lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
	lat_deg = math.degrees(lat_rad)
	return (lat_deg, lon_deg)

def osm_tile_number_to_center_latlon(xtile, ytile, zoom):
  """ Returns the latitude and longitude of the center of a tile, based on the tile numbers and the zoom level"""
  lat1, lon1 = osm_tile_number_to_latlon(xtile, ytile, zoom)
  lat2, lon2 = osm_tile_number_to_latlon(xtile +1 , ytile + 1, zoom)
  return ((lat1 + lat2)/2.0, (lon1 +lon2) / 2.0)

def osm_get_raw_data_by_bounding_box(lat_min, lon_min, lat_max, lon_max):
    return osm_query('https://www.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f' % (lon_min,lat_min,lon_max,lat_max))


def osm_get_raw_data_by_tile_numbers(zoom, x, y):
    NW_corner = osm_tile_number_to_latlon(x, y, zoom)
    lat_max, lon_min = NW_corner
    SE_corner = osm_tile_number_to_latlon(x + 1, y + 1, zoom)
    lat_min, lon_max = SE_corner
    return osm_get_raw_data_by_bounding_box(lat_min, lon_min, lat_max, lon_max)

#TODO Implement caching with max age...
@cached_call
def osm_query(url):
    buffer = StringIO()
    c = pycurl.Curl()
    c.setopt(c.URL, url)
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()

    body = buffer.getvalue()

    return body



# Extract the GPS coordinates of the roads
# roadSel parameter to pass a list of target road names
# printNames optionnal parameter to print all the detected roads
def extract_roads_from_osm_xml(xml):
	soup = BeautifulSoup(xml)
	Roads = []

	Coordinates = {}

	for point in soup.osm.findAll('node'):
		Coordinates[point['id']] = (float(point['lat']), float(point['lon']))

	for way in soup.osm.findAll(lambda nd : nd.name=="way" and nd.findAll(k='highway')):
		name = ""
		road = []

		nodes = way.findAll('nd')

		#Get the road Name
		for u in nodes[-1].findAll('tag'):
			if u['k'] == 'name':
				name =  u['v']

		for node in nodes:
			road.append(Coordinates[node['ref']])
		Roads.append(road)
	return Roads


def osm_get_streets_for_tiles(target_tiles, osm_zoom):
    retval = []

    for x, y in target_tiles:
        osm_xml = osm_get_raw_data_by_tile_numbers(osm_zoom, x, y)
        for street in extract_roads_from_osm_xml(osm_xml):
            if street not in retval:
                retval.append(street)

    return retval

def osm_get_streets(lat_min, lon_min, lat_max, lon_max):
    osm_xml = osm_get_raw_data_by_bounding_box(lat_min, lon_min, lat_max, lon_max)
    return extract_roads_from_osm_xml(osm_xml)

def osm_get_streets_for_source(src_id, osm_zoom):
    client = database.getClient()
    db = client.trace_database
    fs = GridFS(db)

    gps_points = []

    # Iterate source events and group GPS and sensor information
    point_collection = client.point_database.sensors.find({'sourceId':ObjectId(src_id)})

    for point in point_collection:
    	if point['sensorType'] == 'GPS':
            GPS = point['sensorValue']
            gps_points.append(GPS)

    tiles = set([osm_latlon_to_tile_number(lat, lon, osm_zoom) for lat, lon in gps_points])

    streets = osm_get_streets_for_tiles(tiles, osm_zoom)
    return streets



def extract_intersections_from_osm_xml(osm_xml):
    """
        Extract the GPS coordinates of the roads intersections
	Return a list of gps tuples
    """

    soup = BeautifulSoup(osm_xml)

    retval = []
    segments_by_extremities = {}
    Roads = []
    RoadRefs = []
    Coordinates = {}

    for point in soup.osm.findAll('node'):
        Coordinates[point['id']] = (float(point['lat']), float(point['lon']))

    for way in soup.osm.findAll(lambda node : node.name=="way" and node.findAll(k='highway')):
        name = ""
        roadPoints = []

        nodes = way.findAll('nd')
        for node in nodes:
            roadPoints.append(node['ref'])

        RoadRefs.append(roadPoints)

    # iterate over the list of street and over each segment of a street.
    # for each segment extremity, build a list of segment leading to it
    for roadIdx, roadRef in enumerate(RoadRefs):
        for segIdx, seg in enumerate(roadRef):
            coords = Coordinates[seg]
            if coords not in segments_by_extremities:
                segments_by_extremities[coords] = []

            segments_by_extremities[coords].append([roadIdx, segIdx])

    # Iterate over the extremity lists, only keep the ones with at least three segments leading to them
    # Otherwise, they are not an intersection, just a turn in a road
    for k in segments_by_extremities.keys():
        if len(segments_by_extremities[k]) <2:
            del(segments_by_extremities[k])

    #finally return just the keys
    return segments_by_extremities.keys()


def osm_get_intersections_for_tiles(target_tiles, osm_zoom):
    retval = []

    for x, y in target_tiles:
        osm_xml = osm_get_raw_data_by_tile_numbers(osm_zoom, x, y)
        for street in extract_intersections_from_osm_xml(osm_xml):
            if street not in retval:
                retval.append(street)

    return retval

def osm_get_intersections_for_source(src_id, osm_zoom):
    client = database.getClient()
    db = client.trace_database
    fs = GridFS(db)

    gps_points = []

    # Iterate source events and group GPS and sensor information
    point_collection = client.point_database.sensors.find({'sourceId':ObjectId(src_id)})

    for point in point_collection:
    	if point['sensorType'] == 'GPS':
            GPS = point['sensorValue']
            gps_points.append(GPS)

    tiles = set([osm_latlon_to_tile_number(lat, lon, osm_zoom) for lat, lon in gps_points])

    intersections = osm_get_intersections_for_tiles(tiles, osm_zoom)
    return intersections


def pointStyle(name, color, size, stroke_color = '#00000000', stroke_size = 0):
    retval = "'%s': new ol.style.Style({\n\
          image: new ol.style.Circle({\n\
            radius: %d,\n\
            fill: new ol.style.Fill({color: '%s'}),\n\
            stroke: new ol.style.Stroke({ \n\
	            color: '%s', \n\
        	    width: %d \n\
          	}) \n\
          })\n\
        })" % (name, size, color, stroke_color, stroke_size)

    return retval

