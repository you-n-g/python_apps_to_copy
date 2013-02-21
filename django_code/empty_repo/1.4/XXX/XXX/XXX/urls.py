#!/usr/bin/env python
# -*- coding:utf8 -*-
from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'XXX.views.home', name='home'),
    # url(r'^XXX/', include('XXX.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()
urlpatterns += patterns('',
    url(r'^%s(?P<path>.*)$' % settings.MEDIA_URL.lstrip('/'), 'django.views.static.serve', {
        'document_root': settings.MEDIA_ROOT,
    }),
)
