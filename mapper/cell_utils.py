
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
from pyspark.sql import SparkSession
from gridfs import GridFS
from bson.objectid import ObjectId
import numpy as np

from storage import database
from mapper.utils import meterDist, osm_latlon_to_tile_number, osm_get_streets_for_tiles


#given a list of points (a, b, c), returns [(a, b), (b, c)]
def pointsToSegList(pts):
	retval = []

	if len(pts) > 0:
		l = pts[0]
		for p in pts[1:]:
			retval.append((l, p))
			l = p

	return retval

def generateCells(inp, osm_zoom):
	retval = []

        if len(inp) == 2:
            # Always sort the two input points by latitude then longitude
            # This ways, a given segment always generates the same cells, whatever the order
            if inp[0][0] != inp[1][0]:
                start = min(inp, key = lambda x : x[0])
                end = max(inp, key = lambda x : x[0])
            else:
                start = min(inp, key = lambda x : x[1])
                end = max(inp, key = lambda x : x[1])

            points = []

	    dist = int(meterDist(start, end))

            #If the two points are closer than 1 meter ( the cell size), return a single cell
            if dist < 1:
        	tile = osm_latlon_to_tile_number(start[0], start[1], osm_zoom)
		retval.append({"gps":start, "tile":tile, "segment":(start[0], start[1], end[0], end[1])})
            else:
        	    # Place cell every meter on the segment.
        	    for i in range(dist):
	        	x = (float(i) * start[0] + float(dist - i) * end[0]) / dist
		        y = (float(i) * start[1] + float(dist - i) * end[1]) / dist

        		tile = osm_latlon_to_tile_number(x, y, osm_zoom)

                        #Store segment as a 4-tuple (x1, y1, x2, y2)
		        retval.append({"gps":(x, y), "tile":tile, "segment":(start[0], start[1], end[0], end[1])})

	return retval

def sensorValueToTile(inp, osm_zoom):
    (lat, lon), value, timestamp = inp
    tile = osm_latlon_to_tile_number(lat, lon, osm_zoom)
    return [(tile, ((lat, lon), value, timestamp))]


def shareCellWithNeighbours(cell):
    retval = []
    tileX, tileY = cell['tile']

    for x in [-1, 0, 1]:
        for y in [-1, 0, 1]:
            retval.append([(tileX + x, tileY + y), (cell['gps'], cell['segment'])])

    return retval

def place_datapoint_on_cell(inp):
    retval = []
    cell_coords, ([sensor_gps, value, timestamp], cells) = inp

    best_dist = float('inf')
    best_cell_gps = (-1, -1)
    best_cell_segment = []

    for cell_gps, cell_segment in cells:
        distance = meterDist(sensor_gps, cell_gps)
        if distance < best_dist:
            best_cell_gps = cell_gps
            best_dist = distance
            best_cell_segment = cell_segment

    retval.append({
            'cell_gps':best_cell_gps,
            'sensor_gps':sensor_gps, #TKE only keeping that to plot figures of correction process... will most probably be ditched
            'vTimestamp':timestamp,
            'sensorValue':value,
            'segment':best_cell_segment,
        }
    )

    return retval

def segment_equality(seg1, seg2):
    retval = True

    #Check if points from seg1 are in seg2
    for point in seg1:
        if point not in seg2:
            retval = False

    #Ensure that both segments are actual segments (len = 2), or both are degenerate (len=1)
    retval = retval and len(set(seg1)) == len(set(seg2))

    return retval

def averageCell(cell):
    average = 0
    gps, data = cell

    for ts, sensorValue in data:
        average += sensorValue

    average /= float(len(data))

    return (gps, average)

def generateInterpolatedCells(cell_couple):
    retval = []
    cell_1, cell_2 = cell_couple

    segment_1 = (
                    (cell_1['segment'][0], cell_1['segment'][1]),
                    (cell_1['segment'][2], cell_1['segment'][3])
    )
    segment_2 = (
                    (cell_2['segment'][0], cell_2['segment'][1]),
                    (cell_2['segment'][2], cell_2['segment'][3])
    )

    if segment_equality(segment_1, segment_2):
	dist = int(meterDist(cell_1['cell_gps'], cell_2['cell_gps']))
        # Place cell every meter between the current and previous points on the segment.
	for i in range(1,dist - 1):
	    x = (float(i) * cell_1['cell_gps'][0] + float(dist - i) * cell_2['cell_gps'][0]) / dist
	    y = (float(i) * cell_1['cell_gps'][1] + float(dist - i) * cell_2['cell_gps'][1]) / dist
            retval.append({
                'cell_gps':(x, y),
            })
	else:
	    # Check for connected segments (TODO : further away connections ?)
	    # Since segments are different because of the comparison above,
            # only one match maximum can happen
	    for pt1 in segment_1:
	        for pt2 in segment_2:
		    if pt1 == pt2:
                        #Segments are connected, place cells every meters between cell_1 and the intersection point, and between cell_2 and the intersection point
			dist = int(meterDist(cell_1['cell_gps'], pt1))
                        for i in range(1,dist): # This also matches the intersetcion
			    x = (float(dist - i) * cell_1['cell_gps'][0] + float(i) * pt1[0]) / dist
			    y = (float(dist - i) * cell_1['cell_gps'][1] + float(i) * pt1[1]) / dist
                            retval.append({
                                'cell_gps':(x, y),
                            })
			dist = int(meterDist(pt2, cell_2['cell_gps']))
                        for i in range(1,dist - 1): # This does not
			    x = (float(dist - i) * pt2[0] + float(i) * cell_2['cell_gps'][0]) / dist
			    y = (float(dist - i) * pt2[1] + float(i) * cell_2['cell_gps'][1]) / dist
                            retval.append({
                                'cell_gps':(x, y),
                            })

    # Fill returned cells with interpolated timestamps and values
    # The values we are interpolating are not part of retval, hence the division by len(retval) + 2)
    # This only works because retval is already sorted from cell_1 to cell_2
    for cInd in range(len(retval)):
        interpolated_timestamp = (float(len(retval) - i) * cell_1['vTimestamp'] + float(i) * cell_2['vTimestamp']) / (len(retval) + 2)
        interpolated_value = (float(len(retval) - i) * cell_1['sensorValue'] + float(i) * cell_2['sensorValue']) / (len(retval) + 2)

        retval[cInd]['vTimestamp'] = interpolated_timestamp
        retval[cInd]['sensorValue'] = interpolated_value


    actual_retval = []
    #TKE TODO rename silly retval and actual_retval
    for dct in retval:
        actual_retval.append((dct['cell_gps'], (dct['vTimestamp'], dct['sensorValue'])))

    return actual_retval


def get_cells_for_source(src_id, sensorType, osm_zoom, cell_interpolation_function):
    client = database.getClient()
    db = client.trace_database
    fs = GridFS(db)

    gps_points = []

    # Iterate source events and group GPS and sensor information
    point_collection = client.point_database.sensors.find({'sourceId':ObjectId(src_id)})

    GPS = (-1,-1)
    sensor_points = []
    for point in point_collection:
    	if point['sensorType'] == 'GPS':
            GPS = point['sensorValue']
            gps_points.append(GPS)
	elif point['sensorType'] == sensorType:
	    if GPS != (-1, -1):
	        sensor_points.append([GPS, point['sensorValue'], point['vTimestamp']])

    target_tiles = set([osm_latlon_to_tile_number(lat, lon, osm_zoom) for lat, lon in gps_points])
    streets = osm_get_streets_for_tiles(target_tiles, osm_zoom)

    spark = SparkSession.builder.appName("cell generator") \
        .config("spark.driver.extraClassPath", "/home/tanguy/src/spark/mongo-spark/target/scala-2.11/mongo-spark-connector_2.11-2.2.0.jar:/usr/share/java/mongodb-driver-core.jar:/usr/share/java/mongodb-driver.jar:/usr/share/java/bson.jar") \
        .config('spark.executor.cores', '5') \
        .config('spark.cores.max', '5') \
        .config('spark.driver.memory', '8g') \
        .getOrCreate()

    street_rdd = spark.sparkContext.parallelize(streets)
    segments = street_rdd.flatMap(pointsToSegList)
    cells = segments.flatMap(lambda x : generateCells(x, osm_zoom))

    sensor_points_rdd = spark.sparkContext.parallelize(sensor_points)
    tiled_sensor_point_rdd = sensor_points_rdd.flatMap(lambda x : sensorValueToTile(x, osm_zoom))

    # Build list of cells grouped by Osm Tile coordinates, these lists contain cells from the indicated tile, or a neighbouring one.
    neighbouring_cells = cells.flatMap(shareCellWithNeighbours).groupByKey()

    # This grouping now done, we can now compare a sensor mesurement with the cells present in his surroundings (his cell + the neigbouring one) to find the closest one
    located_data_points = tiled_sensor_point_rdd.join(neighbouring_cells).flatMap(place_datapoint_on_cell)

    # Group the measurement points by two (a point and the next) in order to later parralelize the interpolation
    sensor_point_couples = []
    last_sensor = None
    for sensor in sorted(located_data_points.toLocalIterator(), key = lambda x : x['vTimestamp']):
        if last_sensor is not None:
            sensor_point_couples.append([last_sensor, sensor])
        last_sensor = sensor

    # Actually create interpolated measurement cells.
    interpolated_points = spark.sparkContext.parallelize(sensor_point_couples).flatMap(cell_interpolation_function).groupByKey()

    client.close()

    # This changes the returned value to a regular list, making is saveable in database for caching
    # return [cell for  cell  in averaged_points.toLocalIterator()]
    return [(cell, [value for value in vIterator]) for  cell, vIterator  in interpolated_points.toLocalIterator()]

def getMergedCells(traceType, sensorType, osm_zoom, average_cell_values = True, cell_interpolation_function=generateInterpolatedCells):
    retval = []
    cell_values = {}
    client = database.getClient()
    db = client.trace_database
    fs = GridFS(db)


    for traceFile in fs.find():
	if 'sourceTypes' in traceFile.metadata and traceType in traceFile.metadata['sourceTypes']:
            src_cells = get_cells_for_source(traceFile._id, sensorType, osm_zoom, cell_interpolation_function)
            for gps, values in src_cells:
                if tuple(gps) not in cell_values:
                    cell_values[tuple(gps)] = []
                cell_values[tuple(gps)] += [value for ts, value in values]

    #TODO : averaging and groupByKey done by spark...
    for gps in cell_values:
        if average_cell_values:
            retval.append((gps, np.mean(cell_values[gps])))
        else:
            retval.append((gps, cell_values[gps]))

    client.close()

    return retval
