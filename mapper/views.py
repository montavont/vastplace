# -*- coding: utf-8 -*-
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


from django.shortcuts import render
from django.http import HttpResponseNotFound
from django.http import HttpResponse
from bson.objectid import ObjectId
from gridfs import GridFS

import os
import sqlite3
import threading
from threading import Thread


from storage import database

def viewmap(request, fileId):
	response = None
	client = database.getClient()
	db = client.trace_database
	fs = GridFS(db)
	if fs.exists(_id=ObjectId(fileId)):
		traceFile = fs.get(ObjectId(fileId))
		if 'sourceTypes' not in traceFile.metadata or len(traceFile.metadata['sourceTypes']) == 0:
			response = HttpResponse('<h1>Pick at least 1 source type to generate a map</h1>')
		else:
			point_collection = client.point_database.sensors.find({'sourceId':ObjectId(fileId), 'sensorType':"GPS"})
			points = [u['sensorValue'][::-1] for u in point_collection] #OpenLayers uses Lon, Lat order
			responseData = {'trajectories':[{'points': points, 'id':fileId}]}
			if not traceFile.metadata["source_processed"]: # processing unfinished, add a reload info
				responseData['reload_action'] = "refresh"
				responseData['reload_content'] = "2"
			response = render(request, 'mapper/map.html', responseData)
	else:
		response = HttpResponseNotFound('<h1>Source file not found</h1>')

	client.close()
	return response
