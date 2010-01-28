# -*- coding: utf-8 -*-
from django.contrib.admin import *

class ButtonableModelAdmin(ModelAdmin):
	"""
	A subclass of this admin will let you add buttons (like history) in the
	change view of an entry.

	ex.
	class FooAdmin(ButtonableModelAdmin):
	...

	def bar(self, obj):
		obj.bar()
	bar.short_description='Example button'

	buttons = [ bar ]

	you can then put the following in your admin/change_form.html template:

	{% block object-tools %}
	{% if change %}{% if not is_popup %}
	<ul class="object-tools">
	{% for button in buttons %}
	 <li><a href="{{ button.func_name }}/">{{ button.short_description }}</a></li>
	{% endfor %}
	<li><a href="history/" class="historylink">History</a></li>
	{% if has_absolute_url %}<li><a href="../../../r/{{ content_type_id }}/{{ object_id }}/" class="viewsitelink">View on site</a></li>{% endif%}
	</ul>
	{% endif %}{% endif %}
	{% endblock %}
	
	"""
	
	buttons=[]
	change_form_template = 'buttonable_change_form.html'
	
	def change_view( self, request, object_id, extra_context={} ):
		extra_context['buttons'] = self.buttons
		return super(ButtonableModelAdmin, self).change_view( request, object_id, extra_context )
	
	def get_urls( self ):
		parenturls = super(ButtonableModelAdmin, self).get_urls()
		
		from django.conf.urls.defaults import patterns, url
		from django.utils.functional   import update_wrapper
		
		def wrap(view):
			def wrapper(*args, **kwargs):
				return self.admin_site.admin_view(view)(*args, **kwargs)
			return update_wrapper(wrapper, view)
		
		
		for btn in self.buttons:
			btname = btn.__name__
			
			info = self.model._meta.app_label, self.model._meta.module_name, btname
			
			parenturls.insert( 4,
				url(	r'^(.+)/%s/$' % btname,
					wrap( getattr( self, btname ) ),
					name="%s_%s_%s" % info
					)
				)
		
		return parenturls

