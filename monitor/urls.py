"""monitor URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.8/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
import domain, os
from django.conf import settings
from django.conf.urls.static import static

print(settings.STATIC_ROOT)
urlpatterns = [
    url(r'^domain$', 'domain.views.index', name="index"),
    url(r'^ip$','domain.views.getIP',name='getIP'),
    url(r'^getTopData/(?P<index>\d+)/(?P<size>\d+)$','domain.views.getTopData',name='getTopData'),
    url(r'^searchTopData/(?P<keywords>\w+)$','domain.views.searchTopData',name='searchTopData'),
    url(r'^getDomainDetail/(?P<id>\d+)$', 'domain.views.getDomainDetail', name="getDomainDetail"),
    url(r'^getDomainTimeData/(?P<id>\d+)$','domain.views.getDomainTimeData',name='getDomainTimeData'),
    url(r'^getDomainStatusData/(?P<id>\d+)$','domain.views.getDomainStatusData',name='getDomainStatusData'),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', include(admin.site.urls)),
]#+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
