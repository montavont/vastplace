from functools import wraps
from pymongo import MongoClient
from gridfs import GridFS


def cached_call(view_func):
    def _decorator(request, *args, **kwargs):
	client = MongoClient()
	cached_func_call =  client.centraldb.cached_results.find_one({'function':view_func.__name__, 'parameters':[request] + list(args), 'kwargs':kwargs})
	if cached_func_call is not None and 'cached_response' in cached_func_call:
		response = cached_func_call['cached_response']
	else:
	        response = view_func(request, *args, **kwargs)
		client.centraldb.cached_results.insert_one({'function':view_func.__name__, 'parameters':[request] + list(args), 'cached_response':response, 'kwargs':kwargs})
        return response

    return wraps(view_func)(_decorator)
