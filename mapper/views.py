# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.http import HttpResponseNotFound

from pymongo import MongoClient
from bson.objectid import ObjectId
from gridfs import GridFS

import os
import sqlite3
import threading
from threading import Thread


from database_parser.sqlite_parser import sqlite_parser

def populatePointDatabase(fileId):
	client = MongoClient()
	file_db = client.trace_database
	fs = GridFS(file_db)
	traceFile = fs.get(ObjectId(fileId))


	#Copy the original db file
	outF = open('/tmp/mongo_tmpfile' + fileId, 'w')
	line = traceFile.readline()
	while len(line) > 0:
		outF.write(line)
		line = traceFile.readline()
	outF.close()

	# Iterate the content of original file 
	# Will be mved to a parser module
	point_db = client.point_database
	
	parser = sqlite_parser('/tmp/mongo_tmpfile' + fileId)
	for ts, lat, lon in parser.getGPSLocationEvents():
		if 0 not in (lat, lon):
			point_db.sensors.insert_one({
				"sourceId":fileId,
    				"sensorName" : "wi2meR",
				"sensorID" : "IMEI",
    				"vTimestamp" : float(ts)/1000,
				"tstype" : "epoch",
				"sensorType" : "GPS",
    				"sensorValue" : (lat, lon)
				})

	outF.close()

	file_db.fs.files.update_one({'_id': ObjectId(fileId)}, {'$set': {'metadata.processed': 1}})
	os.remove('/tmp/mongo_tmpfile' + fileId)


def viewmap(request, fileId):
	response = None
	client = MongoClient()
	db = client.trace_database
	fs = GridFS(db)
	if fs.exists(_id=ObjectId(fileId)):
		traceFile = fs.get(ObjectId(fileId))
		if traceFile.metadata["processed"]:
			#extract points
			point_collection = client.point_database.sensors.find({'sourceId':fileId, 'sensorType':"GPS"})
			points = [u['sensorValue'][::-1] for u in point_collection] #OpenLayers uses Lon, Lat order
			response = render(request, 'mapper/map.html', {'points': points, 'id':fileId})
		else:
	        	t = threading.Thread(target=populatePointDatabase, args = ([fileId]))
			t.start()
			response = render(request, 'mapper/wip.html')
	else:
		response = HttpResponseNotFound('<h1>Source file not found</h1>')

	return response
