# -*- coding: utf-8 -*-

from django.conf		import settings
from django.conf.urls.defaults	import patterns, include

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	# Example:
	# (r'^pyweb/', include('pyweb.foo.urls')),

	# Uncomment the admin/doc line below and add 'django.contrib.admindocs'
	# to INSTALLED_APPS to enable admin documentation:
	# (r'^admin/doc/', include('django.contrib.admindocs.urls')),

	# Uncomment the next line to enable the admin:
	(r'^admin/', include(admin.site.urls)),
	
	(r'nodes/',  include('openvpn.urls')),
)


if "rosetta" in settings.INSTALLED_APPS:
	urlpatterns += patterns( '',
		( r'rosetta/', include( 'rosetta.urls' ) )
	)

# Development stuff
if settings.DEBUG:
	urlpatterns += patterns('',
		(r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:],
		'django.views.static.serve',
		{'document_root': settings.MEDIA_ROOT, 'show_indexes': True} ),
	)
