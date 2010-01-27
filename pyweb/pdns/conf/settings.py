# -*- coding: utf-8 -*-

from django.conf import settings

SERVER_FQDN         = getattr( settings, "PDNS_SERVER_FQDN" )
HOSTMASTER_MAILADDR = getattr( settings, "PDNS_HOSTMASTER_MAILADDR" )

DEFAULT_TTL         = getattr( settings, "PDNS_DEFAULT_TTL", 3600 )

DEFAULT_DOMAIN_TYPE = getattr( settings, "PDNS_DEFAULT_DOMAIN_TYPE", 'MASTER' )

DEFAULT_RECORD_TYPE = getattr( settings, "PDNS_DEFAULT_RECORD_TYPE", 'A' )

DEFAULT_SOA_REFRESH = getattr( settings, "PDNS_DEFAULT_SOA_REFRESH", 10800 )
DEFAULT_SOA_RETRY   = getattr( settings, "PDNS_DEFAULT_SOA_RETRY",    3600 )
DEFAULT_SOA_EXPIRE  = getattr( settings, "PDNS_DEFAULT_SOA_EXPIRE", 604800 )

