from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from document_api.models import Document

class Command(BaseCommand):
    help = 'Fix documents stuck in processing or modifying status'

    def handle(self, *args, **options):
        # Find documents stuck for more than 5 minutes
        cutoff_time = timezone.now() - timedelta(minutes=5)
        
        stuck_docs = Document.objects.filter(
            status__in=['processing', 'modifying'],
            uploaded_at__lt=cutoff_time
        )
        
        count = 0
        for doc in stuck_docs:
            doc.status = 'failed'
            doc.save()
            count += 1
            self.stdout.write(f'Fixed document: {doc.original_filename}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully fixed {count} stuck documents')
        )