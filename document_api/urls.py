from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('admin/', admin.site.urls),
    path('api/documents/', views.list_documents, name='list_documents'),
    path('api/upload/', views.upload_document, name='upload_document'),
    path('api/status/<uuid:document_id>/', views.get_document_status, name='document_status'),
    path('api/modify/<uuid:document_id>/', views.modify_document_request, name='modify_document'),
    path('api/download/<uuid:document_id>/', views.download_modified_document, name='download_modified'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)