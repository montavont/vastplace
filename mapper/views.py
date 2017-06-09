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


def populatePointDatabase(fileId):
	client = MongoClient()
	file_db = client.trace_database
	fs = GridFS(file_db)
	traceFile = fs.get(ObjectId(fileId))


	#Copy the original db file
	outF = open('/tmp/mongotest' + fileId, 'w')
	line = traceFile.readline()
	while len(line) > 0:
		outF.write(line)
		line = traceFile.readline()
	outF.close()

	# Iterate the content of original file 
	# Will be mved to a parser module
	point_db = client.point_database
	conn = sqlite3.connect('/tmp/mongotest' + fileId)
	c = conn.cursor()
	for u, v in c.execute('SELECT Longitude, Latitude from TRACE').fetchall():
		if 0 not in (u, v):
			point_db.points.insert_one({"sourceId":fileId, 'lon':u, 'lat':v})

	conn.close()
	outF.close()

	file_db.fs.files.update_one({'_id': ObjectId(fileId)}, {'$set': {'metadata.processed': 1}})
	os.remove('/tmp/mongotest' + fileId)


def viewmap(request, fileId):
	response = None
	client = MongoClient()
	db = client.trace_database
	fs = GridFS(db)
	if fs.exists(_id=ObjectId(fileId)):
		traceFile = fs.get(ObjectId(fileId))
		print traceFile.metadata
		if traceFile.metadata["processed"]:
			#extract points
			point_collection = client.point_database.points.find({'sourceId':fileId})
			points = [[u['lon'], u['lat']] for u in point_collection]
			print points
			response = render(request, 'mapper/map.html', {'points': points, 'id':fileId})
		else:
	        	t = threading.Thread(target=populatePointDatabase, args = ([fileId]))
			t.start()
			response = render(request, 'mapper/wip.html')
	else:
		response = HttpResponseNotFound('<h1>Source file not found</h1>')

	return response
