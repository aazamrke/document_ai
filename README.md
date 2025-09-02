# Document Upload API

Django REST Framework API for secure PDF and Word document uploads with processing.

## Features

- Secure file upload with validation
- MIME type verification
- File size limits (10MB)
- Async document processing
- UUID-based file naming
- Status tracking

## API Endpoints

### Upload Document
```
POST /api/upload/
Content-Type: multipart/form-data

Body: file (PDF/DOC/DOCX)
```

### Check Status
```
GET /api/status/{document_id}/
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

3. Start Redis (for Celery):
```bash
redis-server
```

4. Start Celery worker:
```bash
celery -A document_api worker --loglevel=info
```

5. Run Django server:
```bash
python manage.py runserver
```

## Security Features

- File extension validation
- MIME type verification
- File size limits
- UUID-based secure file naming
- Content type validation
- XSS protection headers