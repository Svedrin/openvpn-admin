# -*- coding: utf-8 -*-

import tempfile
import gv

from pygraph.readwrite.dot		import write
from pygraph.classes.Digraph		import digraph
from pygraph.algorithms.searching	import breadth_first_search

from django.http			import HttpResponse

from openvpn.models			import Node, NodeLink

def nodegraph( request ):
	gr = digraph()
	
	for curnode in Node.objects.all():
		gr.add_node( curnode.name, attrs=(
			( "label", r"%s\n%s" % ( curnode.name, curnode.ovpn_subnet ) ),
			( "shape", "diamond" ),
			) )
		
		for client in curnode.client_set.all():
			if client.online:
				color = "green"
			else:
				color = "red"
			
			gr.add_node( client.username, attrs=(
				( "label", r"%s\n%s" % ( client.username, client.ovpn_address ) ),
				( "color", color ),
				( "weight", "10" ),
				) )
			
			gr.add_edge( curnode.name, client.username, attrs=(
				( "dir",    "back" ),
				) )
	
	for curlink in NodeLink.objects.all():
		gr.add_edge( curlink.left.name, curlink.right.name, attrs=(
			( "taillabel", ".%s" %  curlink.left_address.split(".")[3] ),
			( "headlabel", ".%s" % curlink.right_address.split(".")[3] ),
			( "dir", "none" ),
			) )
	
	dot = write(gr)
	gvv = gv.readstring(dot)
	gv.layout(gvv,'dot')
	
	# Yeah. I know. Tell me how libgv accepts file objects please.
	tfile = tempfile.NamedTemporaryFile()
	
	gv.render( gvv, 'png', tfile.name )
	
	tfile.seek(0)
	response = HttpResponse( mimetype='image/png', content=tfile.read() )
	tfile.close()
	
	return response


