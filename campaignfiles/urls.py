from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'upload', views.upload_file, name='upload_file'),
    url(r'content', views.stored_files, name='content'),
    url(r'edit/(?P<fileId>\w+)$', views.edit, name='edit'),
    url(r'delete/(?P<fileId>\w+)$', views.delete, name='delete'),
    url(r'download/(?P<fileId>\w+)$', views.download, name='download'),
    url(r'details/(?P<fileId>\w+)$', views.viewdetails, name='details'),
    url(r'details/(?P<fileIds>[-\w]+)$', views.viewmultipledetails, name='multipledetails'),
]
