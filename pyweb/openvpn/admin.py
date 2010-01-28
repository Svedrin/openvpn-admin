# -*- coding: utf-8 -*-

from django.contrib	import admin

from openvpn.models	import Node, NodeLink


class NodeAdmin( admin.ModelAdmin ):
	list_display   = [ 'name', 'inet_address', 'ovpn_address', 'ovpn_subnet', 'owner' ];
	list_filter    = [ 'owner' ];
	search_fields  = [ 'name', 'ovpn_address', 'ovpn_subnet' ];
	ordering       = [ 'name' ];

admin.site.register( Node, NodeAdmin );


class NodeLinkAdmin( admin.ModelAdmin ):
	list_display   = [ 'left', 'right' ];
	ordering       = [ 'left' ];

admin.site.register( NodeLink, NodeLinkAdmin );
