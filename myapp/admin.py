from django.contrib import admin
from .models import Endpoint, Event  # Import your Event model

class EndpointAdmin(admin.ModelAdmin):
    list_display = ('url', 'api_key', 'reviewed')
    actions = ['approve_custom_js']

    def approve_custom_js(self, request, queryset):
        queryset.update(reviewed=True)
    approve_custom_js.short_description = "Approve selected custom JavaScript"

admin.site.register(Endpoint, EndpointAdmin)
admin.site.register(Event)