from django.contrib import admin

from .models import (
    ResearchProject,
    ResearchTask,
    ResearchResult,
    CompanyProfile,
    WatchlistItem,
)


@admin.register(ResearchProject)
class ResearchProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'status', 'created_at', 'updated_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'user__email', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ResearchTask)
class ResearchTaskAdmin(admin.ModelAdmin):
    list_display = ['company_name', 'task_id', 'status', 'progress', 'started_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['company_name', 'task_id']
    readonly_fields = ['task_id', 'created_at']


@admin.register(ResearchResult)
class ResearchResultAdmin(admin.ModelAdmin):
    list_display = ['task', 'company_validated', 'company_sector', 'created_at']
    list_filter = ['company_validated', 'created_at']
    search_fields = ['task__company_name', 'company_sector']
    readonly_fields = ['created_at']


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'sector', 'research_count', 'last_researched', 'created_at']
    list_filter = ['sector', 'created_at']
    search_fields = ['name', 'sector']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(WatchlistItem)
class WatchlistItemAdmin(admin.ModelAdmin):
    list_display = ['user', 'company', 'alert_on_news', 'alert_on_competitor_change', 'created_at']
    list_filter = ['alert_on_news', 'alert_on_competitor_change', 'created_at']
    search_fields = ['user__email', 'company__name']
    readonly_fields = ['created_at']
