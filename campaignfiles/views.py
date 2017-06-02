# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import Http404
from forms import UploadFileForm

from pymongo import MongoClient
from bson.objectid import ObjectId
from gridfs import GridFS, GridFSBucket

import sqlite3
import threading
from threading import Thread

def index(request):
    return HttpResponse("Nothing to see here yet.")

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
	    fileId = handle_uploaded_file(request.FILES['file'])
	    #t = threading.Thread(target=handle_uploaded_file, args = ([request.FILES['file']]))
	    #t.start()
            return HttpResponseRedirect('/campaignfiles/map/' + str(fileId))
    else:
            return HttpResponseRedirect('/campaignfiles/content')
            #form = UploadFileForm()
    #return render(request, 'campaignfiles/upload.html', {'form': form})

def handle_uploaded_file(inputFile):
	client = MongoClient()
	db = client.trace_database
	fs = GridFSBucket(db)
	
	grid_in = fs.open_upload_stream(str(inputFile))
	for ch in  inputFile.chunks():
		grid_in.write(ch)
	grid_in.close() 

	return ObjectId(grid_in._id)

def stored_files(request):
	client = MongoClient()
	db = client.trace_database
	return render(request, 'campaignfiles/content.html', {'fileList': [{'id':f['_id'], "filename":f["filename"], "length":f["length"]} for f in db.fs.files.find()]})

def download(request, fileId):
	client = MongoClient()
	db = client.trace_database
	fs = GridFS(db)
	if fs.exists(_id=ObjectId(fileId)):
		retfile = fs.get(ObjectId(fileId))
		response = HttpResponse(retfile)
		response['Content-Disposition'] = 'attachment; filename="' + retfile.filename + '"'
		return response
	else:
		raise Http404

def delete(request, fileId):
	client = MongoClient()
	db = client.trace_database
	fs = GridFS(db)
	if fs.exists(_id=ObjectId(fileId)):
		fs.delete(ObjectId(fileId))
		
        return HttpResponseRedirect('/campaignfiles/content')



def viewmap(request, fileId):
	points = [[-122.43, 37.78], [-121.43, 37.78], [-120.43, 37.78], [-119.43, 37.88], ]
	client = MongoClient()
	db = client.trace_database
	fs = GridFS(db)
	if fs.exists(_id=ObjectId(fileId)):
		traceFile = fs.get(ObjectId(fileId))

		outF = open('/tmp/mongotest', 'w')
		line = traceFile.readline()
		while len(line) > 0:
			outF.write(line)
			line = traceFile.readline()

		outF.close()
		conn = sqlite3.connect('/tmp/mongotest')
		c = conn.cursor()

		points = [ [u, v] for u, v in c.execute('SELECT Longitude, Latitude from TRACE').fetchall() if 0 not in (u, v)]

		conn.close()
	
	return render(request, 'campaignfiles/map.html', {'points': points, 'id':fileId})
