from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Document
from .serializers import DocumentUploadSerializer, DocumentSerializer, DocumentModificationSerializer
from .tasks import process_document, modify_document

def index(request):
    """Render the main UI"""
    return render(request, 'index.html')

@api_view(['GET'])
def list_documents(request):
    """List all documents for the UI"""
    documents = Document.objects.all()[:20]  # Limit to 20 recent documents
    serializer = DocumentSerializer(documents, many=True)
    return Response(serializer.data)

@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_document(request):
    """
    Upload and process PDF or Word documents
    """
    serializer = DocumentUploadSerializer(data=request.data)
    
    if serializer.is_valid():
        document = serializer.save()
        
        # Trigger async processing
        process_document.delay(document.id)
        
        response_serializer = DocumentSerializer(document)
        
        # Store in session for UI demo
        if not request.session.get('documents'):
            request.session['documents'] = []
        request.session['documents'].append(response_serializer.data)
        request.session.modified = True
        
        return Response({
            'message': 'Document uploaded successfully',
            'document': response_serializer.data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_document_status(request, document_id):
    """
    Get document processing status
    """
    try:
        document = Document.objects.get(id=document_id)
        serializer = DocumentSerializer(document)
        return Response(serializer.data)
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

@csrf_exempt
@api_view(['POST'])
def modify_document_request(request, document_id):
    """
    Request AI modification of document based on guidelines
    """
    try:
        document = Document.objects.get(id=document_id)
        serializer = DocumentModificationSerializer(data=request.data)
        
        if serializer.is_valid():
            guidelines = serializer.validated_data['guidelines']
            document.modification_guidelines = guidelines
            document.status = 'modifying'
            document.save()
            
            # Direct synchronous modification for testing
            try:
                from .tasks import modify_document_sync
                modify_document_sync(document.id, guidelines)
            except:
                # Fallback to async if sync fails
                modify_document.delay(document.id, guidelines)
            
            return Response({
                'message': 'Document modification requested',
                'document_id': document.id,
                'guidelines': guidelines
            }, status=status.HTTP_202_ACCEPTED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def download_modified_document(request, document_id):
    """
    Download modified document
    """
    try:
        document = Document.objects.get(id=document_id)
        if not document.modified_file:
            return Response({'error': 'Modified document not available'}, status=status.HTTP_404_NOT_FOUND)
        
        from django.http import FileResponse
        import os
        
        # Get the actual filename from modified_file
        modified_filename = os.path.basename(document.modified_file.name)
        
        response = FileResponse(document.modified_file.open(), as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{modified_filename}"'
        
        # Set appropriate content type based on original document type
        if document.content_type == 'application/pdf':
            response['Content-Type'] = 'application/pdf'
        elif document.content_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        else:
            response['Content-Type'] = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            
        return response
    except Document.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)