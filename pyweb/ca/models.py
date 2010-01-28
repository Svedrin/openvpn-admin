# -*- coding: utf-8 -*-

from time			import time, strftime, gmtime
from os.path			import join

from OpenSSL			import crypto
from OpenSSL.crypto		import TYPE_RSA, TYPE_DSA

from django.db			import models
from django.contrib.auth.models import User



class PrivateKey( models.Model ):
	filepath	= models.CharField( "File path", max_length=150 )
	owner		= models.ForeignKey( User, null=True, blank=True )
	
	def __init__( self, *args, **kwargs ):
		models.Model.__init__( self, *args, **kwargs )
		self._privkey = None
	
	def __unicode__( self ):
		return "%s: %s" % ( self.owner, self.filepath )
	
	
	def generate( self, keytype=TYPE_RSA, bits=4096 ):
		self._privkey = crypto.PKey()
		self._privkey.generate_key( keytype, bits )
	
	
	def get_privkey( self ):
		if self._privkey is None:
			if self.id is None:
				self.generate()
			else:
				self.load_keyfile()
		return self._privkey
	
	privkey = property( get_privkey, doc=get_privkey.__doc__ )
	
	
	def load_keyfile( self ):
		fle = open( self.filepath, 'rb' )
		try:
			keydump = fle.read()
			self._privkey = crypto.load_privatekey( crypto.FILETYPE_PEM, keydump )
		finally:
			fle.close()
	
	def save_keyfile( self ):
		fle = open( self.filepath, 'wb' )
		try:
			keydump = crypto.dump_privatekey( crypto.FILETYPE_PEM, self.privkey )
			fle.write( keydump )
		finally:
			fle.close()
	
	def save( self, *args, **kwargs ):
		self.save_keyfile()
		models.Model.save( self, *args, **kwargs )



class Certificate( models.Model ):
	privkey 	= models.ForeignKey( PrivateKey,  null=True, blank=True )
	request 	= models.TextField(  null=True, blank=True )
	certificate	= models.TextField(  null=True, blank=True )
	common_name	= models.CharField(  max_length=200, unique=True )
	owner		= models.ForeignKey( User )
	signed_by	= models.ForeignKey( 'CertAuthority', null=True, blank=True )
	
	def __init__( self, *args, **kwargs ):
		models.Model.__init__( self, *args, **kwargs )
		self._x509req = None
		self._x509    = None
	
	def __unicode__( self ):
		return "%s: %s" % ( self.owner, self.common_name )
	
	def generate_request( self ):
		""" Generate a request from my privkey and commonName. """
		self._x509req = crypto.X509Req()
		self._x509req.set_pubkey( self.privkey.privkey )
		subj = self._x509req.get_subject()
		subj.commonName   = self.common_name
		subj.emailAddress = self.owner.email
	
	def load_request( self ):
		""" Load the certificate request. """
		self._x509req = crypto.load_certificate_request( crypto.FILETYPE_PEM, self.request )
	
	def save_request( self ):
		""" Save the certificate request. """
		self.request = crypto.dump_certificate_request( crypto.FILETYPE_PEM, self._x509req )
		self.save()
	
	def get_x509_request( self ):
		""" Load an existing request or create a new one. """
		if self._x509req is None:
			if self.request:
				self.load_request()
			elif self.privkey:
				self.generate_request()
		
		return self._x509req
	
	x509req = property( get_x509_request, doc=get_x509_request.__doc__ )
	
	
	
	def load_certificate( self ):
		""" Load a certificate. """
		self._x509 = crypto.load_certificate( crypto.FILETYPE_PEM, self.certificate )
	
	def save_certificate( self ):
		""" Save a certificate. """
		self.certificate = crypto.dump_certificate( crypto.FILETYPE_PEM, self._x509 )
		self.save()
	
	def get_x509_certificate( self ):
		""" Return the certificate, and load if necessary. """
		if self._x509 is None:
			self.load_certificate()
		return self._x509
	
	def set_x509_certificate( self, cert ):
		""" Store the given cert as my certificate, if I don't already have one. """
		if not self.certificate and self._x509 is None:
			self._x509 = cert
			self.save()
	
	x509    = property( get_x509_certificate, set_x509_certificate, doc=get_x509_certificate.__doc__ )
	
	
	def save_to_file( self, filepath ):
		fle = open( filepath, 'wb' )
		try:
			fle.write( self.certificate )
		finally:
			fle.close()



class CertAuthority( models.Model ):
	name		= models.CharField( max_length=100 )
	rootcert	= models.ForeignKey( Certificate, null=True, blank=True )
	serial		= models.IntegerField( default=0 )
	owner		= models.ForeignKey( User )
	
	
	def __unicode__( self ):
		return "%s: %s" % ( self.owner, self.name )
	
	def generate_root_certificate( self, ca_path ):
		""" Generate a private key and root certificate for this CA.
		
		    The privkey and cert will be stored in ca_path/ca.{key,cert}.
		"""
		
		privkey = PrivateKey( filepath=join( ca_path, "ca.key" ), owner=self.owner )
		privkey.generate()
		privkey.save()
		
		cacert = Certificate( privkey=privkey, common_name=self.name, owner=self.owner )
		cacert.generate_request()
		
		self._sign( cacert, issuer=cacert.x509req.get_subject(), privkey=privkey.privkey )
		
		cacert.save_certificate()
		cacert.save_to_file( join( ca_path, "ca.cert" ) )
		
		self.rootcert = cacert
		self.save()
	
	
	def _sign( self, certificate, issuer, privkey ):
		cert = crypto.X509()
		cert.set_pubkey( certificate.x509req.get_pubkey() )
		cert.set_subject( certificate.x509req.get_subject() )
		cert.set_issuer( issuer )
		cert.set_notBefore( strftime( '%Y%m%d%H%M%SZ' ) )
		cert.set_notAfter(  strftime( '%Y%m%d%H%M%SZ', gmtime( time() + 60*60*24*365*10 ) ) )
		cert.set_serial_number( self.serial )
		cert.sign( privkey, "SHA1" )
		
		certificate.x509 = cert
		certificate.signed_by = self
		certificate.save_certificate()
		
		self.serial += 1
		self.save()
	
	def sign( self, certificate ):
		""" Load the CSR from a certificate object and create a certificate signed by this CA. """
		
		return self._sign( certificate,
			issuer=self.rootcert.x509.get_subject(),
			privkey=self.rootcert.privkey.privkey
			)




