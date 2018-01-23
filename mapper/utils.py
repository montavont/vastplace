import math


CIRC_EARTH = 40075000
RADIUS_EARTH = 6367000

def meterDist( u, v):
	lat1, lon1, lat2, lon2 = map(math.radians, [u[0], u[1], v[0], v[1]])

	dlon = lon2 - lon1 
	dlat = lat2 - lat1 

	a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
	dist = RADIUS_EARTH * 2 * math.asin(math.sqrt(a)) 

	return dist



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

