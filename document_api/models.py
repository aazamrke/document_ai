from django.db import models
from django.core.validators import FileExtensionValidator
import uuid
import os

def document_upload_path(instance, filename):
    """Generate secure upload path"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('documents', filename)

def modified_document_upload_path(instance, filename):
    """Generate secure upload path for modified documents"""
    ext = filename.split('.')[-1]
    filename = f"modified_{uuid.uuid4()}.{ext}"
    return os.path.join('documents', 'modified', filename)

class Document(models.Model):
    PROCESSING_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('modifying', 'Modifying'),
        ('modified', 'Modified'),
        ('no_changes', 'No Changes Needed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(
        upload_to=document_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=PROCESSING_STATUS, default='pending')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    modified_file = models.FileField(
        upload_to=modified_document_upload_path,
        null=True, blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx'])]
    )
    modification_guidelines = models.TextField(null=True, blank=True)
    modified_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']