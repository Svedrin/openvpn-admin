# -*- coding: utf-8 -*-

from django.conf.urls.defaults import patterns

urlpatterns = patterns(
	'openvpn.views',
	( r'nodes.png', 'nodegraph' ),
	)
