# -*- coding: utf-8 -*-

from myadmin		import admin

from ca.models		import CertAuthority, Certificate, PrivateKey


class PrivateKeyAdmin( admin.ModelAdmin ):
	list_display   = [ 'owner', 'filepath' ];
	list_filter    = [ 'owner' ];
	ordering       = [ 'owner' ];

admin.site.register( PrivateKey, PrivateKeyAdmin );


class CertificateAdmin( admin.ButtonableModelAdmin ):
	list_display   = [ 'owner', 'common_name', 'signed_by' ];
	list_filter    = [ 'owner', 'signed_by' ];
	ordering       = [ 'owner', 'common_name' ];
	
	def sign_button( self, request, object_id ):
		""" Sign a certificate using the CA set in signed_by. """
		obj = Certificate.objects.get( id=object_id )
		obj.signed_by.sign( obj );
		
		return self.change_view( request, object_id )
	
	sign_button.short_description = sign_button.__doc__
	
	buttons        = [ sign_button ];

admin.site.register( Certificate, CertificateAdmin );


class CertAuthorityAdmin( admin.ModelAdmin ):
	list_display   = [ 'owner', 'name' ];
	list_filter    = [ 'owner' ];
	ordering       = [ 'owner', 'name' ];

admin.site.register( CertAuthority, CertAuthorityAdmin );
