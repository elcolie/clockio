from django.contrib import admin

from clockio.memories.models import Memory, MemoryClockOut


class MemoryAdmin(admin.ModelAdmin):
    __basic_fields = ['id', 'clock_in']
    list_display = __basic_fields
    list_display_links = __basic_fields


class MemoryClockOutAdmin(admin.ModelAdmin):
    __basic_fields = ['id', 'clock_out']
    list_display = __basic_fields
    list_display_links = __basic_fields


admin.site.register(Memory, MemoryAdmin)
admin.site.register(MemoryClockOut, MemoryClockOutAdmin)
