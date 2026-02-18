from django.contrib import admin
from .models import University, Course, Module, ResourceType, Resource, ResourceDownload

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'course_count']
    search_fields = ['name', 'code']
    prepopulated_fields = {'code': ('name',)}  # Auto-generate code from name

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'university']
    list_filter = ['university']
    search_fields = ['code', 'name']
    prepopulated_fields = {'code': ('name',)}  # Auto-generate code from name

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'parent_module']
    list_filter = ['course__university', 'course']
    search_fields = ['name']

@admin.register(ResourceType)
class ResourceTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'icon']
    search_fields = ['name']

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'resource_type', 'year', 'downloads']
    list_filter = ['course__university', 'course', 'resource_type', 'year']
    search_fields = ['title', 'description']
    readonly_fields = ['file_size', 'downloads', 'uploaded_at']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Only on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(ResourceDownload)
class ResourceDownloadAdmin(admin.ModelAdmin):
    list_display = ['resource', 'user', 'downloaded_at']
    list_filter = ['downloaded_at']
    readonly_fields = ['downloaded_at']
