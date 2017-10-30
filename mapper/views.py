# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.http import HttpResponseNotFound
from django.http import HttpResponse
from pymongo import MongoClient
from bson.objectid import ObjectId
from gridfs import GridFS

import os
import sqlite3
import threading
from threading import Thread


def viewmap(request, fileId):
	response = None
	client = MongoClient()
	db = client.trace_database
	fs = GridFS(db)
	if fs.exists(_id=ObjectId(fileId)):
		traceFile = fs.get(ObjectId(fileId))
		if 'sourceTypes' not in traceFile.metadata or len(traceFile.metadata['sourceTypes']) == 0:
			response = HttpResponse('<h1>Pick at least 1 source type to generate a map</h1>')
		else:
			point_collection = client.point_database.sensors.find({'sourceId':fileId, 'sensorType':"GPS"})
			points = [u['sensorValue'][::-1] for u in point_collection] #OpenLayers uses Lon, Lat order
			responseData = {'trajectories':[{'points': points, 'id':fileId}]}
			if not traceFile.metadata["source_processed"]: # processing unfinished, add a reload info
				responseData['reload_action'] = "refresh"
				responseData['reload_content'] = "2"
			response = render(request, 'mapper/map.html', responseData)
	else:
		response = HttpResponseNotFound('<h1>Source file not found</h1>')

	return response
