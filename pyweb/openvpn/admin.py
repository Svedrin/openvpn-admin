# -*- coding: utf-8 -*-

from django.contrib	import admin

from openvpn.models	import Node, NodeLink, Client


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


class ClientAdmin( admin.ModelAdmin ):
	list_display   = [ 'username', 'enabled', 'online', 'ovpn_address', 'last_address', 'last_connect', 'last_node' ];
	list_filter    = [ 'enabled' ];
	ordering       = [ 'username' ];

admin.site.register( Client, ClientAdmin );
