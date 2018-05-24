
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
from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

rest_patterns = [
    url(r'trace_count', views.trace_count, name='trace_count'),
    url(r'total_size_b', views.total_size, name='total_size_b'),
    url(r'total_size_kb', views.total_size_kb, name='total_size_kb'),
    url(r'event_count', views.event_count, name='event_count'),
]

rest_patterns = format_suffix_patterns(rest_patterns)


urlpatterns = [
    url(r'upload', views.upload_file, name='upload_file'),
    url(r'content', views.stored_files, name='content'),
    url(r'edit/(?P<fileId>\w+)$', views.edit, name='edit'),
    url(r'delete/(?P<fileId>\w+)$', views.delete, name='delete'),
    url(r'download/(?P<fileId>\w+)$', views.download, name='download'),
    url(r'details/(?P<fileId>\w+)$', views.viewdetails, name='details'),
    url(r'details/(?P<fileIds>[-\w]+)$', views.viewmultipledetails, name='multipledetails'),
] + rest_patterns
