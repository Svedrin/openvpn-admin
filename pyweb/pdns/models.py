# -*- coding: utf-8 -*-

import time

from django.conf		import settings
from django.db			import models
from django.db.models		import Q
from django.contrib.auth.models import User

from pdns.conf			import settings as pdns_settings


class Supermaster(models.Model):
	""" SuperMasters are master servers which are allowed to push domains to us,
	    even if they are not listed with us as a slave domain yet.
	
	    For more info about SuperSlave operation, see:
	    http://downloads.powerdns.com/documentation/html/generic-mypgsql-backends.html#AEN6061
	"""
	
	ip              = models.CharField( max_length=25 )
	nameserver      = models.CharField( 'Name des Nameservers', max_length=255 )
	account         = models.CharField( 'Accountname', max_length=40, unique=True )
	
	def __unicode__(self):
		return self.nameserver
	
	class Meta:
		db_table = 'supermasters'


class Domain(models.Model):
	""" Registers a domain with the server as a NATIVE, MASTER or SLAVE domain.
	
	    In SuperSlave operation, the "account" field will specify which SuperMaster
	    we received this domain from.
	"""
	
	TYPE_CHOICES    = (
		( "NATIVE", "Nativ: Daten aus DB holen, aber nicht zur Replikation freigeben" ),
		( "MASTER", "Master: Wie Nativ, andere Server dürfen replizieren" ),
		( "SLAVE",  "Slave: Replikation von einem Masterserver" ),
		)
	
	name		= models.CharField(     'Name der Domain', max_length=255, unique=True )
	master		= models.CharField(     'Masterserver bei Slaves', max_length=20, blank=True )
	last_check	= models.DateTimeField( 'Datum der letzten Prüfung auf Änderungen', null=True, blank=True, editable=False )
	dtype		= models.CharField(     'Typ', db_column="type", max_length=6, choices=TYPE_CHOICES,
						default=pdns_settings.DEFAULT_DOMAIN_TYPE )
	notified_serial = models.IntegerField(  'Letzte im SOA benutzte Serial', null=True, blank=True, editable=False )
	account 	= models.ForeignKey(    Supermaster, db_column="account", null=True, blank=True, to_field="account" )
	owner		= models.ForeignKey(    User, null=True, blank=True )
	
	def __unicode__(self):
		return self.name
	
	class Meta:
		db_table = 'domains'
	
	soa_record = property(
		lambda self: self.record_set.get( rrtype="SOA" ),
		doc="The SOA record for this domain."
		);
	
	def create_soa_record( self, refresh=None, retry=None, expire=None, default_ttl=None ):
		""" Create or change the SOA record for this domain.
		
		    Calling this method is NOT necessary to update the serial if you changed
		    a record, it is ONLY necessary if anything apart from the serial has changed
		    or no SOA record exists.
		"""
		if self.owner is not None:
			hostmaster = self.owner.email.replace( "@", "." )
		else:
			hostmaster = pdns_settings.HOSTMASTER_MAILADDR;
		
		if refresh     is None: refresh     = pdns_settings.DEFAULT_SOA_REFRESH
		if retry       is None: retry       = pdns_settings.DEFAULT_SOA_RETRY
		if expire      is None: expire      = pdns_settings.DEFAULT_SOA_EXPIRE
		if default_ttl is None: default_ttl = pdns_settings.DEFAULT_TTL
		
		try:
			soa = self.soa_record
		except Record.DoesNotExist:
			soa = self.record_set.create( name="", rrtype="SOA" )
		
		# The SOA record format is "primary-NS hostmaster serial refresh retry expire default_ttl"
		# set serial to 0 to have it auto-assigned by PowerDNS.
		soa.content = "%(primns)s %(hostmaster)s 0 %(refresh)d %(retry)d %(expire)d %(ttl)d" % {
			'primns':     pdns_settings.SERVER_FQDN,
			'hostmaster': hostmaster,
			'refresh':    refresh,
			'retry':      retry,
			'expire':     expire,
			'ttl':        default_ttl,
			}
		
		soa.save()
	
	
	def create_or_update_addr( self, name, address, rrtype="A" ):
		""" Make sure `name` is the only RR in this domain that resolves to `address`. """
		
		self.record_set.filter( ( Q(content=address) | Q(name=name) ) & Q(rrtype=rrtype) ).delete()
		
		rec = self.record_set.create( name=name, rrtype=rrtype, content=address )
		rec.save()
	
	
	def save( self, *args, **kwargs ):
		""" Save the Domain, automatically creating a SOA record for new domains. """
		makeSoa = ( self.id is None )
		models.Model.save( self, *args, **kwargs )
		if makeSoa:
			self.create_soa_record()


class Record(models.Model):
	""" A record for a domain.
	
	    For documentation on the fields, see:
	    http://downloads.powerdns.com/documentation/html/generic-mypgsql-backends.html#AEN5878
	"""
	
	TYPE_CHOICES = (
		( 'A',     'A:     IPv4-Adresse' ),
		( 'AAAA',  'AAAA:  IPv6-Adresse' ),
		( 'CNAME', 'CName: Weiterleitung auf anderen Namen' ),
		( 'PTR',   'PTR:   Hostname für Reverse-DNS-Eintrag' ),
		( 'TXT',   'TXT:   Beliebiger Text' ),
		( 'SOA',   'SOA:   Allgemeine Angaben zur Domain' ),
		( 'MX',    'MX:    Mailserver' ),
		( 'NS',    'NS:    Nameserver' ),
		( 'SRV',   'SRV:   Services' ),
		( 'SPF',   'SPF:   Sender Permitted From' ),
		)
	
	domain		= models.ForeignKey(	Domain )
	name		= models.CharField(	'Name',    max_length=255, blank=True )
	rrtype		= models.CharField(	'Klasse',  max_length=6, db_column="type", choices=TYPE_CHOICES,
						default=pdns_settings.DEFAULT_RECORD_TYPE )
	content 	= models.CharField(	'Eintrag', max_length=255 )
	ttl		= models.IntegerField(  null=True, blank=True, default=pdns_settings.DEFAULT_TTL )
	prio		= models.IntegerField(  null=True, blank=True, default=0 )
	change_date	= models.IntegerField(  editable=False )
	
	def __unicode__(self):
		return "%s (%s: %s)" % ( self.name, self.rrtype, self.content )
	
	class Meta:
		db_table = 'records'
	
	def get_relative_name( self ):
		""" Return the path from the domain name downward. """
		if self.name == self.domain.name:
			return ''
		else:
			domlen = len( self.domain.name )
			return self.name[:-(domlen+1)]
	
	relname = property( get_relative_name, doc=get_relative_name.__doc__ )
	
	def save( self, *args, **kwargs ):
		""" Save the record, making sure the name field contains an FQDN. This will also
		    update the change_date field to tell PowerDNS that it needs to NOTIFY the domain.
		"""
		
		if not self.name.endswith( self.domain.name ):
			if self.name:
				self.name = "%s.%s" % ( self.name, self.domain.name )
			else:
				self.name = self.domain.name
		
		self.change_date = time.time()
		
		models.Model.save( self, *args, **kwargs )


