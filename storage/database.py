
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
