from django.contrib import admin
from django.utils.html import format_html
from .models import University, Course, Module, ResourceType, Resource, ResourceDownload

# ==================== INLINE ADMIN CLASSES ====================

class CourseInline(admin.TabularInline):
    """Show courses directly under university"""
    model = Course
    extra = 1
    fields = ['code', 'name', 'description']
    show_change_link = True

class ModuleInline(admin.TabularInline):
    """Show modules directly under course"""
    model = Module
    extra = 1
    fields = ['name', 'parent_module', 'order']
    show_change_link = True

class ResourceInline(admin.TabularInline):
    """Show resources directly under module"""
    model = Resource
    extra = 1
    fields = ['title', 'resource_type', 'year_level', 'academic_year', 'file']
    show_change_link = True

# ==================== MAIN ADMIN CLASSES ====================

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    """🏛️ University Management"""
    list_display = ['name', 'code', 'course_count_display', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'code', 'description']
    prepopulated_fields = {'code': ('name',)}
    readonly_fields = ['created_at', 'course_count_display']
    
    fieldsets = (
        ('🏛️ Basic Information', {
            'fields': ('name', 'code', 'logo', 'description')
        }),
        ('📊 Statistics', {
            'fields': ('course_count_display', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [CourseInline]
    
    def course_count_display(self, obj):
        count = obj.courses.count()
        url = f"/admin/resources/course/?university__id__exact={obj.id}"
        return format_html('<a href="{}">{} Courses</a>', url, count)
    course_count_display.short_description = "Courses"

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """📚 Course Management"""
    list_display = ['code', 'name', 'university', 'module_count_display', 'resource_count_display']
    list_filter = ['university', 'created_at']
    search_fields = ['code', 'name', 'description']
    list_editable = ['name']
    autocomplete_fields = ['university']
    readonly_fields = ['created_at', 'module_count_display', 'resource_count_display']
    
    fieldsets = (
        ('📚 Course Details', {
            'fields': ('university', 'code', 'name', 'description')
        }),
        ('📊 Statistics', {
            'fields': ('module_count_display', 'resource_count_display', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ModuleInline]
    
    def module_count_display(self, obj):
        count = obj.modules.count()
        url = f"/admin/resources/module/?course__id__exact={obj.id}"
        return format_html('<a href="{}">{} Modules</a>', url, count)
    module_count_display.short_description = "Modules"
    
    def resource_count_display(self, obj):
        count = Resource.objects.filter(course=obj).count()
        url = f"/admin/resources/resource/?course__id__exact={obj.id}"
        return format_html('<a href="{}">{} Resources</a>', url, count)
    resource_count_display.short_description = "Resources"

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    """📁 Module/Folder Management"""
    list_display = ['name', 'course', 'parent_module', 'submodule_count', 'resource_count']
    list_filter = ['course__university', 'course', 'parent_module']
    search_fields = ['name', 'description']
    autocomplete_fields = ['course', 'parent_module']
    readonly_fields = ['created_at', 'submodule_count', 'resource_count', 'path_display']
    
    fieldsets = (
        ('📁 Module Details', {
            'fields': ('course', 'name', 'description', 'parent_module', 'order')
        }),
        ('📊 Statistics', {
            'fields': ('submodule_count', 'resource_count', 'created_at'),
            'classes': ('collapse',)
        }),
        ('📍 Path', {
            'fields': ('path_display',),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ResourceInline]
    
    def submodule_count(self, obj):
        return obj.submodules.count()
    submodule_count.short_description = "Submodules"
    
    def resource_count(self, obj):
        return obj.resource_set.count()
    resource_count.short_description = "Resources"
    
    def path_display(self, obj):
        return format_html('<span style="color: #ffd700;">{}</span>', obj.path)
    path_display.short_description = "Folder Path"

@admin.register(ResourceType)
class ResourceTypeAdmin(admin.ModelAdmin):
    """📄 Resource Type Management"""
    list_display = ['name', 'icon_display', 'resource_count']
    search_fields = ['name']
    
    fieldsets = (
        ('📄 Resource Type', {
            'fields': ('name', 'icon')
        }),
    )
    
    def icon_display(self, obj):
        return format_html('<i class="fas {}" style="font-size: 1.2rem;"></i>', obj.icon)
    icon_display.short_description = "Icon"
    
    def resource_count(self, obj):
        return obj.resource_set.count()
    resource_count.short_description = "Resources"

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """📎 Resource/File Management"""
    list_display = ['title', 'course', 'resource_type', 'year_level_display', 'academic_year', 'downloads', 'file_link']
    list_filter = ['course__university', 'course', 'resource_type', 'year_level', 'academic_year', 'semester']
    search_fields = ['title', 'description']
    autocomplete_fields = ['university', 'course', 'module', 'resource_type', 'uploaded_by']
    readonly_fields = ['file_size', 'downloads', 'uploaded_at', 'file_preview']
    list_editable = ['year_level', 'academic_year']
    list_per_page = 25
    
    fieldsets = (
        ('📎 Resource Details', {
            'fields': ('title', 'description', 'resource_type', 'file', 'file_preview')
        }),
        ('📍 Location', {
            'fields': ('university', 'course', 'module')
        }),
        ('📅 Academic Info', {
            'fields': ('year_level', 'academic_year', 'semester')
        }),
        ('📊 Metadata', {
            'fields': ('file_size', 'downloads', 'uploaded_by', 'uploaded_at'),
            'classes': ('collapse',)
        }),
    )
    
    def year_level_display(self, obj):
        colors = {1: '#4CAF50', 2: '#2196F3', 3: '#FF9800', 4: '#9C27B0', 5: '#F44336'}
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 20px;">{}</span>',
            colors.get(obj.year_level, '#666'),
            obj.get_year_level_display()
        )
    year_level_display.short_description = "Year Level"
    
    def file_link(self, obj):
        return format_html('<a href="{}" target="_blank">📄 View</a>', obj.file.url)
    file_link.short_description = "File"
    
    def file_preview(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank" class="button">📄 Open File</a>',
                obj.file.url
            )
        return "No file uploaded"
    file_preview.short_description = "Preview"
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'university', 'course', 'module', 'resource_type', 'uploaded_by'
        )

@admin.register(ResourceDownload)
class ResourceDownloadAdmin(admin.ModelAdmin):
    """📊 Download Tracking"""
    list_display = ['resource', 'user', 'downloaded_at']
    list_filter = ['downloaded_at']
    readonly_fields = ['downloaded_at']
    list_per_page = 50
    
    fieldsets = (
        ('📊 Download Info', {
            'fields': ('resource', 'user', 'downloaded_at', 'ip_address')
        }),
    )
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False