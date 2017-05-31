# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from forms import UploadFileForm

from pymongo import MongoClient
from gridfs import GridFSBucket

import threading
from threading import Thread

def index(request):
    return HttpResponse("Hello, world. You're at the campaign file index.")


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
	    t = threading.Thread(target=handle_uploaded_file, args = ([request.FILES['file']]))
	    t.start()
            return HttpResponseRedirect('/campaignfiles')
    else:
        form = UploadFileForm()
    return render(request, 'campaignfiles/upload.html', {'form': form})

def handle_uploaded_file(inputFile):
	client = MongoClient()
	db = client.trace_database
	fs = GridFSBucket(db)
	
	grid_in = fs.open_upload_stream(str(inputFile))
	for ch in  inputFile.chunks():
		grid_in.write(ch)
	grid_in.close() 

def stored_files(request):
	files = ["44565", "hellfest", "Rama yade"]
	client = MongoClient()
	db = client.trace_database
	print [f for f in db.fs.files.find()]
	return render(request, 'campaignfiles/content.html', {'fileList': [{'id':f['_id'], "filename":f["filename"], "length":f["length"]} for f in db.fs.files.find()]})

def download(request, fileId):
	print request, fileId
	return HttpResponse("Download")

def delete(request, fileId):
	print request, fileId
	client = MongoClient()
	db = client.trace_database
	return HttpResponse("DELETE")
