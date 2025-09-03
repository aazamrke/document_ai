import pytest
from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status
from .models import Document
from .tasks import ai_modify_text, modify_document_sync
import json

class DocumentModelTest(TestCase):
    def test_document_creation(self):
        """Test document model creation"""
        document = Document.objects.create(
            original_filename="test.pdf",
            file_size=1024,
            content_type="application/pdf"
        )
        assert document.original_filename == "test.pdf"
        assert document.status == "pending"
        assert document.file_size == 1024

class DocumentUploadTest(TestCase):
    def setUp(self):
        self.client = Client()
        
    def test_upload_valid_pdf(self):
        """Test uploading valid PDF file"""
        pdf_content = b"%PDF-1.4 test content"
        uploaded_file = SimpleUploadedFile(
            "test.pdf", 
            pdf_content, 
            content_type="application/pdf"
        )
        
        response = self.client.post('/api/upload/', {'file': uploaded_file})
        assert response.status_code == status.HTTP_201_CREATED
        assert Document.objects.count() == 1
        
    def test_upload_invalid_file_type(self):
        """Test uploading invalid file type"""
        txt_file = SimpleUploadedFile(
            "test.txt", 
            b"test content", 
            content_type="text/plain"
        )
        
        response = self.client.post('/api/upload/', {'file': txt_file})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
    def test_upload_oversized_file(self):
        """Test uploading file exceeding size limit"""
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file = SimpleUploadedFile(
            "large.pdf", 
            large_content, 
            content_type="application/pdf"
        )
        
        response = self.client.post('/api/upload/', {'file': large_file})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

class DocumentModificationTest(TestCase):
    def setUp(self):
        self.document = Document.objects.create(
            original_filename="test.pdf",
            file_size=1024,
            content_type="application/pdf",
            status="completed"
        )
        
    def test_ai_modify_text_formal(self):
        """Test AI text modification with formal guidelines"""
        original_text = "This document don't have proper grammar."
        guidelines = "make it formal"
        
        modified_text, changes_made = ai_modify_text(original_text, guidelines)
        
        assert changes_made == True
        assert "do not" in modified_text
        
    def test_ai_modify_text_grammar(self):
        """Test AI text modification with grammar guidelines"""
        original_text = "We recieve alot of feedback about this."
        guidelines = "fix grammar"
        
        modified_text, changes_made = ai_modify_text(original_text, guidelines)
        
        assert changes_made == True
        assert "receive" in modified_text
        assert "a lot" in modified_text
        
    def test_ai_modify_text_no_changes(self):
        """Test AI modification when no changes needed"""
        original_text = "This is a perfect sentence."
        guidelines = "fix grammar"
        
        modified_text, changes_made = ai_modify_text(original_text, guidelines)
        
        assert changes_made == False
        
    def test_modify_document_sync(self):
        """Test synchronous document modification"""
        result = modify_document_sync(self.document.id, "make it formal")
        
        self.document.refresh_from_db()
        assert self.document.status in ['modified', 'no_changes']

class DocumentAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.document = Document.objects.create(
            original_filename="test.pdf",
            file_size=1024,
            content_type="application/pdf",
            status="completed"
        )
        
    def test_list_documents(self):
        """Test listing documents API"""
        response = self.client.get('/api/documents/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]['original_filename'] == "test.pdf"
        
    def test_get_document_status(self):
        """Test getting document status"""
        response = self.client.get(f'/api/status/{self.document.id}/')
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data['status'] == 'completed'
        
    def test_modify_document_request(self):
        """Test document modification request"""
        response = self.client.post(
            f'/api/modify/{self.document.id}/',
            data=json.dumps({'guidelines': 'make it formal'}),
            content_type='application/json'
        )
        assert response.status_code == status.HTTP_202_ACCEPTED
        
    def test_modify_nonexistent_document(self):
        """Test modifying non-existent document"""
        response = self.client.post(
            '/api/modify/999/',
            data=json.dumps({'guidelines': 'make it formal'}),
            content_type='application/json'
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

class DocumentStatusTest(TestCase):
    def test_status_transitions(self):
        """Test document status transitions"""
        document = Document.objects.create(
            original_filename="test.pdf",
            file_size=1024,
            content_type="application/pdf"
        )
        
        # Initial status
        assert document.status == "pending"
        
        # Update to processing
        document.status = "processing"
        document.save()
        assert document.status == "processing"
        
        # Update to completed
        document.status = "completed"
        document.save()
        assert document.status == "completed"