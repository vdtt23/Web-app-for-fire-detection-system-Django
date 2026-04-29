from django.contrib import admin
from .models import SensorData

# Register your models here.

@admin.register(SensorData)
class SensorDataAdmin(admin.ModelAdmin):
    list_display = ('node_id', 'temperature', 'smoke', 'humidity', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('node_id',)
    ordering = ('-created_at',)