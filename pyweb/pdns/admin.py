# -*- coding: utf-8 -*-

from django.contrib	import admin

from pdns.models	import Supermaster, Domain, Record

class SupermasterAdmin( admin.ModelAdmin ):
	list_display   = [ 'account', 'ip', 'nameserver' ];
	search_fields  = [ 'ip', 'nameserver', 'account' ];
	ordering       = [ 'account' ];

admin.site.register( Supermaster, SupermasterAdmin );


class DomainAdmin( admin.ModelAdmin ):
	list_display   = [ 'name', 'dtype', 'last_check', 'account', 'owner' ];
	list_filter    = [ 'name' ];
	search_fields  = [ 'name' ];
	ordering       = [ 'name' ];

admin.site.register( Domain, DomainAdmin );


class RecordAdmin( admin.ModelAdmin ):
	list_display   = [ 'name', 'rrtype', 'content', 'ttl', 'prio' ];
	list_filter    = [ 'domain' ];
	search_fields  = [ 'name', 'content' ];
	ordering       = [ 'name' ];

admin.site.register( Record, RecordAdmin );
