from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'map/(?P<fileId>\w+)$', views.viewmap, name='map'),
]
