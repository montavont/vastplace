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
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseNotFound

from bson.objectid import ObjectId
from gridfs import GridFS, GridFSBucket
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view


from campaignfiles.forms import UploadFileForm
from campaignfiles.models import SourceType
from multiprocessing import Process
import importlib

from storage import database

def index(request):
    return HttpResponse("Nothing to see here yet.")

def upload_file(request):
    response = None
    fileIds = []
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
                for upFile in request.FILES.getlist('file'):
                        fileId = handle_uploaded_file(upFile)
                        fileIds.append(fileId)
                response = HttpResponseRedirect('/campaignfiles/details/' + '-'.join(str(fId) for fId in fileIds))
    else:
            response = HttpResponseRedirect('/campaignfiles/content')

    return response


#Callback on file upload
def handle_uploaded_file(inputFile):

        #Store file in database as is
        client = database.getClient()
        db = client.trace_database
        fs = GridFSBucket(db)

        grid_in = fs.open_upload_stream(str(inputFile), metadata={"source_processed":0})
        for ch in  inputFile.chunks():
                grid_in.write(ch)
        grid_in.close()

        #Process file in order to convert its data to standard format
        p = Process(None, target=SourceProcessingProcess, args = ([grid_in._id]))
        p.start()

        client.close()

        return ObjectId(grid_in._id)

#Trigger in order to convert a source into
def SourceProcessingProcess(fileId):
        client = database.getClient()
        file_db = client.trace_database
        fs = GridFS(file_db)
        traceFile = fs.get(ObjectId(fileId))

        file_db.processing_lock.create_index("fileId", unique = True)
        file_db.metric_lock.delete_one({'fileId':fileId })

        point_db = client.point_database

        trace_types = []
        if 'sourceTypes' in traceFile.metadata:
                trace_types = traceFile.metadata['sourceTypes']
        all_types = SourceType.objects.all()
        parsers = []

        for t in all_types:
                if t.sourceType in trace_types:
                        _module = importlib.import_module(t.module + ".parsing")
                        _class = getattr(_module, t.parserClass)
                        parsers.append(_class(fileId))

        for parser in parsers:
                for event in  parser.getEvents():
                        point_db.sensors.insert_one(event)


        file_db.fs.files.update_one({'_id': ObjectId(fileId)}, {'$set': {'metadata.source_processed': 1}})

        file_db.metric_lock.delete_one({'fileId':fileId })
        client.close()


def stored_files(request):
        client = database.getClient()
        db = client.trace_database
        fs = GridFS(db)
        responseData = {'fileList': []}

        for traceFile in fs.find():
            types = "none"
            if 'sourceTypes' in traceFile.metadata:
                types = ','.join([t for t in traceFile.metadata['sourceTypes']])
            responseData['fileList'].append(
                {
                    'id':traceFile._id,
                    "filename":traceFile.filename,
                    "length":traceFile.length,
                    "types":types
                }
            )

        client.close()
        return render(request, 'campaignfiles/content.html', responseData)

def download(request, fileId):
        response = HttpResponseNotFound('<h1>File not found</h1>')
        client = database.getClient()
        db = client.trace_database
        fs = GridFS(db)
        if fs.exists(_id=ObjectId(fileId)):
                retfile = fs.get(ObjectId(fileId))
                response = HttpResponse(retfile)
                response['Content-Disposition'] = 'attachment; filename="' + retfile.filename + '"'
        client.close()
        return response


def delete(request, fileId):
        client = database.getClient()
        db = client.trace_database
        fs = GridFS(db)
        if fs.exists(_id=ObjectId(fileId)):
                fs.delete(ObjectId(fileId))

        point_db = client.point_database
        point_db.sensors.delete_many({"sourceId":fileId})
        point_db.wifiscanresults.delete_many({"sourceId":fileId})

        client.close()
        return HttpResponseRedirect('/campaignfiles/content')



def viewdata(request, fileId):
        client = database.getClient()
        file_db = client.trace_database
        fs = GridFS(file_db)
        traceFile = fs.get(ObjectId(fileId))

        point_db = client.point_database

        trace_types = []
        if 'sourceTypes' in traceFile.metadata:
                trace_types = traceFile.metadata['sourceTypes']
        all_types = SourceType.objects.all()
        analyzers = []

        for t in all_types:
                if t.sourceType in trace_types:
                        _module = importlib.import_module(t.module + ".views")
                        _function = getattr(_module, "view_data")
                        analyzers.append(_function)


        return analyzers[0](request, ObjectId(fileId))

def viewdetails(request, fileId):
        responseData = {'id':fileId}

        client = database.getClient()
        db = client.trace_database
        fs = GridFS(db)
        traceFile = fs.get(ObjectId(fileId))

        for k in ['phoneuser', 'phoneId', 'notes']:
                if k in traceFile.metadata:
                        responseData[k] = traceFile.metadata[k]

        responseData['sourceTypes']= []
        enabled_types = []
        if 'sourceTypes' in traceFile.metadata:
                enabled_types = traceFile.metadata['sourceTypes']

        all_types = SourceType.objects.values_list('sourceType', flat = True)
        for t in all_types:
                if t in enabled_types:
                        responseData['sourceTypes'].append({'name':t, 'enabled':"checked"})
                else:
                        responseData['sourceTypes'].append({'name':t, 'enabled':''})

        client.close()
        return render(request, 'campaignfiles/details.html', responseData)



def viewmultipledetails(request, fileIds):
        responseData = {'ids':[]}
        for fileId in fileIds.split('-'):
                if len(fileId) > 0:
                        responseData['ids'].append(fileId)

        return render(request, 'campaignfiles/multidetails.html', responseData)



def edit(request, fileId):
        client = database.getClient()
        db = client.trace_database
        reprocessSource = False


        for k in ['phoneuser', 'phoneId', 'notes']:
                db.fs.files.update_one({'_id': ObjectId(fileId)}, {'$set': {'metadata.' + k: request.POST[k]}})


        #Check if source types changed
        types = SourceType.objects.values_list('sourceType', flat = True)
        fs = GridFS(db)
        traceFile = fs.get(ObjectId(fileId))
        previous_types = []
        if 'sourceTypes' in traceFile.metadata:
                previous_types = traceFile.metadata['sourceTypes']
        enabled_types = []
        for t in types:
                if t in request.POST and 'on' in request.POST[t]:
                        if t not in previous_types:
                                reprocessSource = True
                        enabled_types.append(t)

        db.fs.files.update_one({'_id': ObjectId(fileId)}, {'$set': {'metadata.sourceTypes' : enabled_types}})

        #Trigger processings if types changed
        if reprocessSource:
                db.fs.files.update_one({'_id': ObjectId(fileId)}, {'$set': {'metadata.source_processed': 0}})
                p = Process(None, target=SourceProcessingProcess, args = ([fileId]))
                p.start()

        client.close()

        return viewdetails(request, fileId)



@api_view(['GET'])
def trace_count (request):

	client = database.getClient()
	fs = GridFS(client.trace_database)
	count = fs.find().count()
	return Response(count, status=status.HTTP_200_OK)

@api_view(['GET'])
def total_size (request):

        size = 0
	client = database.getClient()
	fs = GridFS(client.trace_database)
        for traceFile in fs.find():
            size += traceFile.length

	return Response(size, status=status.HTTP_200_OK)

@api_view(['GET'])
def total_size_kb (request):

        size = 0
	client = database.getClient()
	fs = GridFS(client.trace_database)
        for traceFile in fs.find():
            size += traceFile.length

	return Response(size / 1000, status=status.HTTP_200_OK)

@api_view(['GET'])
def event_count (request):
	client = database.getClient()
        event_count = client.point_database.sensors.find().count()
	return Response(event_count, status=status.HTTP_200_OK)
