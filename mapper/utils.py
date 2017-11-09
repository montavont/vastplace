from math import radians, cos, sin, asin, sqrt


CIRC_EARTH = 40075000
RADIUS_EARTH = 6367000

def meterDist( u, v):
	lat1, lon1, lat2, lon2 = map(radians, [u[0], u[1], v[0], v[1]])

	dlon = lon2 - lon1 
	dlat = lat2 - lat1 

	a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
	dist = RADIUS_EARTH * 2 * asin(sqrt(a)) 

	return dist

