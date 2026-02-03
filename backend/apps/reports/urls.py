from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SavedReportViewSet,
    ReportTemplateViewSet,
    ShareReportView,
    ExportReportView,
)

router = DefaultRouter()
router.register(r'saved', SavedReportViewSet, basename='saved-report')
router.register(r'templates', ReportTemplateViewSet, basename='report-template')

urlpatterns = [
    path('', include(router.urls)),
    path('shared/<uuid:share_token>/', ShareReportView.as_view(), name='share-report'),
    path('export/', ExportReportView.as_view(), name='export-report'),
]
