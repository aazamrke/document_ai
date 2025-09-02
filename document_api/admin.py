from django.contrib import admin
from .models import Document

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['id', 'original_filename', 'status', 'file_size', 'uploaded_at']
    list_filter = ['status', 'content_type', 'uploaded_at']
    search_fields = ['original_filename', 'id']
    readonly_fields = ['id', 'uploaded_at', 'processed_at']