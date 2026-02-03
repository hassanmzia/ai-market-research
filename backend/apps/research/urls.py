from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ResearchProjectViewSet,
    ResearchTaskViewSet,
    CompanyProfileViewSet,
    WatchlistViewSet,
    CompanySearchView,
    ResearchHistoryView,
)

router = DefaultRouter()
router.register(r'projects', ResearchProjectViewSet, basename='research-project')
router.register(r'tasks', ResearchTaskViewSet, basename='research-task')
router.register(r'companies', CompanyProfileViewSet, basename='company-profile')
router.register(r'watchlist', WatchlistViewSet, basename='watchlist')

urlpatterns = [
    path('', include(router.urls)),
    path('search/', CompanySearchView.as_view(), name='company-search'),
    path('history/', ResearchHistoryView.as_view(), name='research-history'),
]
