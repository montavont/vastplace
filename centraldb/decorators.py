
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
from functools import wraps
from gridfs import GridFS, GridFSBucket
from bson import ObjectId
import json

from storage import database



def cached_call(view_func):
    def _decorator(request, *args, **kwargs):
	client = database.getClient()
	db = client.centraldb
        response = None

	cached_func_call =  db.cached_results.find_one({'function':view_func.__name__, 'parameters':[request] + list(args), 'kwargs':kwargs})
	if cached_func_call is not None and 'grid_id' in cached_func_call:
                fs = GridFS(db)
                response = json.loads(fs.get(ObjectId(cached_func_call['grid_id'])).read())
	else:
                fs_bucket = GridFSBucket(db)
	        response = view_func(request, *args, **kwargs)
                grid_in = fs_bucket.open_upload_stream("z")
                grid_in.write(json.dumps(response))
                grid_in.close()

		db.cached_results.insert_one({'function':view_func.__name__, 'parameters':[request] + list(args), 'grid_id':ObjectId(grid_in._id), 'kwargs':kwargs})

	client.close()
        return response

    return wraps(view_func)(_decorator)
