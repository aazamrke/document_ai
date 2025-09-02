from rest_framework import serializers
from .models import Document
try:
    import magic
except ImportError:
    magic = None

class DocumentUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField()
    
    class Meta:
        model = Document
        fields = ['file']
    
    def validate_file(self, value):
        # File size validation (10MB limit)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB")
        
        # MIME type validation
        allowed_types = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ]
        
        # MIME type validation
        if magic:
            # Read file content to verify MIME type
            file_content = value.read()
            value.seek(0)  # Reset file pointer
            
            try:
                mime_type = magic.from_buffer(file_content, mime=True)
                if mime_type not in allowed_types:
                    raise serializers.ValidationError("Invalid file type. Only PDF and Word documents are allowed.")
            except:
                # Fallback to content type if magic fails
                if value.content_type not in allowed_types:
                    raise serializers.ValidationError("Invalid file type. Only PDF and Word documents are allowed.")
        else:
            # Fallback validation without magic
            if value.content_type not in allowed_types:
                raise serializers.ValidationError("Invalid file type. Only PDF and Word documents are allowed.")
        
        return value
    
    def create(self, validated_data):
        file = validated_data['file']
        document = Document.objects.create(
            file=file,
            original_filename=file.name,
            file_size=file.size,
            content_type=file.content_type
        )
        return document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'original_filename', 'file_size', 'content_type', 'status', 'uploaded_at', 'processed_at', 'modified_file', 'modification_guidelines', 'modified_at']

class DocumentModificationSerializer(serializers.Serializer):
    guidelines = serializers.CharField(max_length=2000, help_text="Guidelines for document modification")