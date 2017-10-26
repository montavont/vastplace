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
import importlib

from campaignfiles.models import SourceType


def populatePointDatabase(fileId):
	client = MongoClient()
	file_db = client.trace_database
	fs = GridFS(file_db)
	traceFile = fs.get(ObjectId(fileId))


	#Copy the original db file
	outPath = '/tmp/mongo_tmpfile_' + fileId
	outF = open(outPath, 'w')
	line = traceFile.readline()
	while len(line) > 0:
		outF.write(line)
		line = traceFile.readline()
	outF.close()

	# Iterate the content of original file 
	# Will be mved to a parser module
	point_db = client.point_database
	
        

	trace_types = []                                        
        if 'sourceTypes' in traceFile.metadata:                                
                trace_types = traceFile.metadata['sourceTypes']
	all_types = SourceType.objects.all()
	parsers = []

	for t in all_types:
		if t.sourceType in trace_types:
			_module = importlib.import_module(t.parsingModule)
			_class = getattr(_module, t.parserClass)
			parsers.append(_class(outPath))

	for parser in parsers:
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


		for ts, scanInd, bssid, ssid, channel, level, capabilities in parser.getScanResults():
			point_db.wifiscanresults.insert_one({
					"sourceId":fileId,
    					"sensorName" : "wi2meR",
					"sensorID" : "IMEI",
    					"vTimestamp" : float(ts)/1000,
					"tstype" : "epoch",
					"sensorType" : "wifi scan result",
    					"sensorValue" : {
						"bssid" : bssid,
						"ssid" : ssid,
						"rssi" : level, 
						"channel" : channel, 
						"capabilities" : capabilities,
						"scan index": scanInd,
						},
					})
		
	file_db.fs.files.update_one({'_id': ObjectId(fileId)}, {'$set': {'metadata.source_processed': 1}})
	os.remove(outPath)



def viewmap(request, fileId):
	response = None
	client = MongoClient()
	db = client.trace_database
	fs = GridFS(db)
	if fs.exists(_id=ObjectId(fileId)):
		traceFile = fs.get(ObjectId(fileId))
        	if 'sourceTypes' in traceFile.metadata and len(traceFile.metadata['sourceTypes']) > 0:
			#This is done to avoid having two parrallel threads, but must be done better...
			if client.point_database.sensors.count({'sourceId':fileId}) > 0:
				#extract points
				point_collection = client.point_database.sensors.find({'sourceId':fileId, 'sensorType':"GPS"})
				points = [u['sensorValue'][::-1] for u in point_collection] #OpenLayers uses Lon, Lat order
				responseData = {'points': points, 'id':fileId}
				if not traceFile.metadata["source_processed"]: # processing unfinished, add a reload info
					responseData['reload_action'] = "refresh"
					responseData['reload_content'] = "2"
				response = render(request, 'mapper/map.html', responseData)
			else:
	        		t = threading.Thread(target=populatePointDatabase, args = ([fileId]))
				t.start()
				response = render(request, 'mapper/wip.html')
		else:
			response = HttpResponseNotFound('<h1>No source Type specified. Select one and save.</h1>')
	else:
		response = HttpResponseNotFound('<h1>Source file not found</h1>')

	return response
