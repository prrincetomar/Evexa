from django.contrib import admin
from .models import Event, EventRegistration, Tag
from .models import EventVisibilitySettings

admin.site.register(Event)
admin.site.register(EventRegistration)
admin.site.register(Tag)

@admin.register(EventVisibilitySettings)
class EventVisibilitySettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Only ONE settings row allowed
        return not EventVisibilitySettings.objects.exists()