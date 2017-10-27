# -*- coding: utf-8 -*-

from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import HttpResponseNotFound

from pymongo import MongoClient
from bson.objectid import ObjectId
from gridfs import GridFS, GridFSBucket

from forms import UploadFileForm
from models import SourceType
from multiprocessing import Process
import importlib

def index(request):
    return HttpResponse("Nothing to see here yet.")

def upload_file(request):
    response = None
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
	    fileId = handle_uploaded_file(request.FILES['file'])
            response = HttpResponseRedirect('/campaignfiles/details/' + str(fileId))
    else:
            response = HttpResponseRedirect('/campaignfiles/content')

    return response


#Callback on file upload
def handle_uploaded_file(inputFile):

	#Store file in database as is
	client = MongoClient()
	db = client.trace_database
	fs = GridFSBucket(db)
	
	grid_in = fs.open_upload_stream(str(inputFile), metadata={"source_processed":0})
	for ch in  inputFile.chunks():
		grid_in.write(ch)
	grid_in.close() 

	#Process file in order to convert its data to standard format
	p = Process(None, target=SourceProcessingProcess, args = ([grid_in._id]))
	p.start()


	return ObjectId(grid_in._id)
		
#Trigger in order to convert a source into 
def SourceProcessingProcess(fileId):
	client = MongoClient()
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
			_module = importlib.import_module(t.parsingModule)
			_class = getattr(_module, t.parserClass)
			parsers.append(_class(fileId))

	for parser in parsers:
		for event in  parser.getEvents():
			point_db.sensors.insert_one(event)
	

	file_db.fs.files.update_one({'_id': ObjectId(fileId)}, {'$set': {'metadata.source_processed': 1}})

	file_db.metric_lock.delete_one({'fileId':fileId })


def stored_files(request):
        client = MongoClient()
        db = client.trace_database
        print [u['filename'] for u in db.fs.files.find()]
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
                raise HttpResponseNotFound('<h1>File not found</h1>')


def delete(request, fileId):
        client = MongoClient()
        db = client.trace_database
        fs = GridFS(db)
        if fs.exists(_id=ObjectId(fileId)):
                fs.delete(ObjectId(fileId))

        point_db = client.point_database
        point_db.sensors.delete_many({"sourceId":fileId})
        point_db.wifiscanresults.delete_many({"sourceId":fileId})

        return HttpResponseRedirect('/campaignfiles/content')





def viewdetails(request, fileId):
	responseData = {'id':fileId}

	client = MongoClient()
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

	return render(request, 'campaignfiles/details.html', responseData)



def edit(request, fileId):
        client = MongoClient()
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
		db.fs.files.update_one({'_id': ObjectId(fileId)}, {'$set': {'metadata.source_processed': 1}})
		p = Process(None, target=SourceProcessingProcess, args = ([fileId]))
		p.start()

        return viewdetails(request, fileId)


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
