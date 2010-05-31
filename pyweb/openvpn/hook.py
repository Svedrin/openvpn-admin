#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Set this to the same path you used in settings.py, or None for auto-detection.
OPENVPN_ADMIN_ROOT = '/srv/geek-net.de/admin';

### DO NOT CHANGE ANYTHING BELOW THIS LINE ###

import os, sys
from os.path import join, dirname, abspath, exists

# environment variables
sys.path.append( OPENVPN_ADMIN_ROOT )
sys.path.append( join( OPENVPN_ADMIN_ROOT, 'pyweb' ) )
os.environ['DJANGO_SETTINGS_MODULE'] = 'pyweb.settings'


# If you get an error about Python not being able to write to the Python
# egg cache, the egg cache path might be set awkwardly. This should not
# happen under normal circumstances, but every now and then, it does.
# Uncomment this line to point the egg cache to /tmp.
#os.environ['PYTHON_EGG_CACHE'] = '/tmp/pyeggs'



from datetime			import datetime

from openvpn.models		import Node, Client

from ca.models			import Certificate


def hook_client_connect( my_address, common_name, inet_address, ovpn_address ):
	try:
		node   = Node.objects.get( ovpn_address=my_address )
	except Node.DoesNotExist:
		return 5
	
	try:
		cert   = Certificate.objects.get( common_name=common_name )
	except Certificate.DoesNotExist:
		return 4
	
	try:
		client = cert.owner.client
	except Client.DoesNotExist:
		return 3
	
	if not client.enabled:
		return 1
	
	client.ovpn_address = ovpn_address
	client.last_address = inet_address
	client.last_connect = datetime.now()
	client.last_node    = node
	client.online = True
	client.save()
	
	if node.inet_domain:
		node.inet_domain.create_or_update_addr(
			name=("%s.%s" % ( common_name, node.inet_domain.name )), address=inet_address, rrtype='A'
			)
	
	if node.ovpn_domain:
		node.ovpn_domain.create_or_update_addr(
			name=("%s.%s" % ( common_name, node.ovpn_domain.name )), address=ovpn_address, rrtype='A'
			)
	
	return 0


def hook_client_disconnect( my_address, common_name, inet_address, ovpn_address ):
	try:
		node   = Node.objects.get( ovpn_address=my_address )
	except Node.DoesNotExist:
		return 0
	
	try:
		cert   = Certificate.objects.get( common_name=common_name )
	except Certificate.DoesNotExist:
		return 0
	
	try:
		client = cert.owner.client
	except Client.DoesNotExist:
		return 0
	
	if node.inet_domain:
		node.inet_domain.delete_addr(
			name=("%s.%s" % ( common_name, node.inet_domain.name )), address=inet_address, rrtype='A'
			)
	
	if node.ovpn_domain:
		node.ovpn_domain.delete_addr(
			name=("%s.%s" % ( common_name, node.ovpn_domain.name)), address=ovpn_address, rrtype='A'
			)
	
	client.online = False
	client.save()
	
	return 0


if __name__ == '__main__':
	stat = {
	  'client-connect':	hook_client_connect,
	  'client-disconnect':	hook_client_disconnect,
	}[ os.environ['script_type'] ](
		my_address   = os.environ['ifconfig_local'],
		common_name  = os.environ['common_name'],
		inet_address = os.environ['trusted_ip'],
		ovpn_address = os.environ['ifconfig_pool_remote_ip'],
	)
	
	sys.exit( stat )


