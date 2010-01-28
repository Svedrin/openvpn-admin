# -*- coding: utf-8 -*-

import re

from django.db			import models
from django.contrib.auth.models import User

from pdns.models		import Domain, Record

from ca.models			import Certificate


# TODO: client-connect-script für OpenVPN bauen.
# das Script kriegt den CommonName und die IP des Clients als Env-Vars, und
# einen Dateinamen für eine Config für diesen Client als $1.
# wenn exit-status != 0, wird der Client disconnected -> enabled-Feld checken.
# Env-Variablen:
#   common_name (cname des certs, mit dem sich der Benutzer authentifiziert hat)
#   script_type (als welches script werde ich ausgeführt)
#   trusted_ip  (ip des clients)


class Node(models.Model):
	""" A Node is a VPN endpoint that provides VPN access to a whole network. """
	
	name		= models.CharField( 'Name des Nodes',               max_length=100, unique=True )
	inet_address	= models.CharField( 'Adresse/Hostname im Internet', max_length=50,  unique=True )
	ovpn_address	= models.CharField( 'Adresse im VPN',               max_length=15,  unique=True, blank=True )
	ovpn_subnet	= models.CharField( 'gehosteter Adressbereich',     max_length=18,  unique=True, blank=True )
	owner		= models.ForeignKey(   User, null=True, blank=True )
	certificate	= models.ForeignKey( Certificate )
	
	def __unicode__( self ):
		if self.ovpn_subnet:
			return "%s (%s)" % ( self.name, self.ovpn_subnet )
		else:
			return self.name
	
	def update_dns_domains( self ):
		""" Check the DNS records. """
		
		pattern = re.compile( '^(\d{1,3}\.){3}[1-9]\d{0,2}$' )
		if pattern.match( self.inet_address ) == None:
			rrtype = 'CNAME'
		else:
			rrtype = 'A'
		
		real = Domain.objects.get(  name="nodes.geek-net.de" )
		real.create_or_update_addr( name=("%s.nodes.geek-net.de" % self.name), address=self.inet_address, rrtype=rrtype )
		
		if self.ovpn_address:
			virt = Domain.objects.get(  name="gnet" )
			virt.create_or_update_addr( name=("%s.nodes.gnet" % self.name), address=self.ovpn_address, rrtype="A" )


class NodeLink(models.Model):
	""" A Link between two Nodes, interconnecting two subnets of the VPN. """
	
	left		= models.ForeignKey( Node, related_name='nodelink_left_set' )
	right		= models.ForeignKey( Node, related_name='nodelink_right_set' )
	left_address	= models.IPAddressField( 'Adresse links',  max_length=50, unique=True )
	right_address	= models.IPAddressField( 'Adresse rechts', max_length=50, unique=True )
	
	def __unicode__( self ):
		return u"%s ←→ %s" % ( self.left.name, self.right.name )


class Client(User):
	""" A Client connecting to one of the Nodes to get VPN access. """
	
	enabled 	= models.BooleanField( default=True )
	last_address	= models.IPAddressField( 'last connected IP',       editable=False, null=True, blank=True )
	last_connect	= models.DateTimeField(  'last connect time',       editable=False, null=True, blank=True )
	last_node	= models.ForeignKey( Node, null=True, blank=True )


