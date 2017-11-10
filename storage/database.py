from django.conf import settings
from pymongo import MongoClient

from mongobox import MongoBox


# This class stubs calls the the pymongo client and replaces them with mongobox temporary memory database when running tests.

box = None


def getClient():
	global box
	if settings.TESTING:
		if box is None:
			box = MongoBox()
			box.start()

		retval = box.client()
	else:
		retval = MongoClient()

	return retval

import json

def purge_database():
	global box
	if settings.TESTING and box is not None:
		client = box.client()
	        for db in client.database_names():
			if db in ['admin', 'startup_log']:
				continue
			else:
				for collection in client[db].collection_names():
					client[db].drop_collection(collection)
