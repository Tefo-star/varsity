from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import University, Course, Module, ResourceType, Resource, ResourceDownload

# ==================== INLINE ADMIN CLASSES ====================

class CourseInline(admin.TabularInline):
    """Show courses directly under university"""
    model = Course
    extra = 0
    fields = ['code', 'name', 'module_count_display', 'resource_count_display']
    readonly_fields = ['module_count_display', 'resource_count_display']
    show_change_link = True
    classes = ['collapse']
    
    def module_count_display(self, obj):
        count = obj.modules.count()
        url = reverse('admin:resources_module_changelist') + f'?course__id__exact={obj.id}'
        return format_html('<a href="{}">{} Modules</a>', url, count)
    module_count_display.short_description = "Modules"
    
    def resource_count_display(self, obj):
        count = Resource.objects.filter(course=obj).count()
        url = reverse('admin:resources_resource_changelist') + f'?course__id__exact={obj.id}'
        return format_html('<a href="{}">{} Resources</a>', url, count)
    resource_count_display.short_description = "Resources"

class ModuleInline(admin.TabularInline):
    """Show modules directly under course"""
    model = Module
    extra = 0
    fields = ['name', 'parent_module', 'order', 'resource_count_display']
    readonly_fields = ['resource_count_display']
    show_change_link = True
    classes = ['collapse']
    
    def resource_count_display(self, obj):
        count = obj.resource_set.count()
        url = reverse('admin:resources_resource_changelist') + f'?module__id__exact={obj.id}'
        return format_html('<a href="{}">{} Resources</a>', url, count)
    resource_count_display.short_description = "Resources"

class ResourceInline(admin.TabularInline):
    """Show resources directly under module"""
    model = Resource
    extra = 0
    fields = ['title', 'resource_type', 'year_level', 'academic_year', 'downloads', 'file_link']
    readonly_fields = ['downloads', 'file_link']
    show_change_link = True
    classes = ['collapse']
    
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">📄 View</a>', obj.file.url)
        return "No file"
    file_link.short_description = "File"

# ==================== MAIN ADMIN CLASSES ====================

@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    """🏛️ UNIVERSITY MANAGEMENT - Top Level"""
    
    # List Display
    list_display = [
        'name', 
        'code', 
        'course_count_display', 
        'resource_count_display',
        'created_at'
    ]
    
    list_filter = ['created_at']
    search_fields = ['name', 'code', 'description']
    prepopulated_fields = {'code': ('name',)}
    readonly_fields = ['created_at', 'course_count_display', 'resource_count_display']
    inlines = [CourseInline]
    
    # Fieldsets for Add/Edit page
    fieldsets = (
        ('🏛️ Basic Information', {
            'fields': ('name', 'code', 'logo', 'description'),
            'description': 'Core university details'
        }),
        ('📊 Statistics', {
            'fields': ('course_count_display', 'resource_count_display', 'created_at'),
            'classes': ('collapse',),
            'description': 'Overview of content under this university'
        }),
    )
    
    def course_count_display(self, obj):
        count = obj.courses.count()
        url = reverse('admin:resources_course_changelist') + f'?university__id__exact={obj.id}'
        return format_html('<a href="{}" style="font-weight: bold;">{} Courses</a>', url, count)
    course_count_display.short_description = "📚 Courses"
    
    def resource_count_display(self, obj):
        count = Resource.objects.filter(course__university=obj).count()
        url = reverse('admin:resources_resource_changelist') + f'?course__university__id__exact={obj.id}'
        return format_html('<a href="{}" style="font-weight: bold;">{} Total Resources</a>', url, count)
    resource_count_display.short_description = "📄 Resources"

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    """📚 COURSE MANAGEMENT - Second Level"""
    
    list_display = [
        'code', 
        'name', 
        'university_link',
        'module_count_display', 
        'resource_count_display',
        'created_at'
    ]
    
    list_filter = ['university', 'created_at']
    search_fields = ['code', 'name', 'description']
    list_editable = ['name']
    autocomplete_fields = ['university']
    readonly_fields = ['created_at', 'module_count_display', 'resource_count_display']
    inlines = [ModuleInline]
    
    fieldsets = (
        ('📚 Course Details', {
            'fields': ('university', 'code', 'name', 'description'),
            'description': 'Basic course information'
        }),
        ('📊 Content Overview', {
            'fields': ('module_count_display', 'resource_count_display', 'created_at'),
            'classes': ('collapse',),
            'description': 'Modules and resources in this course'
        }),
    )
    
    def university_link(self, obj):
        url = reverse('admin:resources_university_change', args=[obj.university.id])
        return format_html('<a href="{}">🏛️ {}</a>', url, obj.university.name)
    university_link.short_description = "University"
    university_link.admin_order_field = 'university__name'
    
    def module_count_display(self, obj):
        count = obj.modules.count()
        url = reverse('admin:resources_module_changelist') + f'?course__id__exact={obj.id}'
        return format_html('<a href="{}" style="font-weight: bold;">{} Modules</a>', url, count)
    module_count_display.short_description = "📁 Modules"
    
    def resource_count_display(self, obj):
        count = Resource.objects.filter(course=obj).count()
        url = reverse('admin:resources_resource_changelist') + f'?course__id__exact={obj.id}'
        return format_html('<a href="{}" style="font-weight: bold;">{} Resources</a>', url, count)
    resource_count_display.short_description = "📄 Resources"

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    """📁 MODULE/FOLDER MANAGEMENT - Third Level"""
    
    list_display = [
        'name', 
        'course_link',
        'parent_module_link',
        'submodule_count_display',
        'resource_count_display',
        'order'
    ]
    
    list_filter = ['course__university', 'course', 'parent_module']
    search_fields = ['name', 'description']
    autocomplete_fields = ['course', 'parent_module']
    readonly_fields = ['created_at', 'submodule_count', 'resource_count', 'path_display']
    inlines = [ResourceInline]
    
    fieldsets = (
        ('📁 Module Details', {
            'fields': ('course', 'name', 'description', 'parent_module', 'order'),
            'description': 'Module/folder information'
        }),
        ('📍 Path Location', {
            'fields': ('path_display',),
            'classes': ('collapse',),
        }),
        ('📊 Content', {
            'fields': ('submodule_count', 'resource_count', 'created_at'),
            'classes': ('collapse',),
        }),
    )
    
    def course_link(self, obj):
        url = reverse('admin:resources_course_change', args=[obj.course.id])
        return format_html('<a href="{}">📚 {}</a>', url, obj.course.code)
    course_link.short_description = "Course"
    course_link.admin_order_field = 'course__code'
    
    def parent_module_link(self, obj):
        if obj.parent_module:
            url = reverse('admin:resources_module_change', args=[obj.parent_module.id])
            return format_html('<a href="{}">📁 {}</a>', url, obj.parent_module.name)
        return "—"
    parent_module_link.short_description = "Parent Folder"
    
    def submodule_count_display(self, obj):
        count = obj.submodules.count()
        if count > 0:
            url = reverse('admin:resources_module_changelist') + f'?parent_module__id__exact={obj.id}'
            return format_html('<a href="{}">{} Subfolders</a>', url, count)
        return "0"
    submodule_count_display.short_description = "📁 Subfolders"
    
    def submodule_count(self, obj):
        return obj.submodules.count()
    submodule_count.short_description = "Total Submodules"
    
    def resource_count_display(self, obj):
        count = obj.resource_set.count()
        if count > 0:
            url = reverse('admin:resources_resource_changelist') + f'?module__id__exact={obj.id}'
            return format_html('<a href="{}" style="font-weight: bold;">{} Resources</a>', url, count)
        return "0"
    resource_count_display.short_description = "📄 Resources"
    
    def resource_count(self, obj):
        return obj.resource_set.count()
    resource_count.short_description = "Total Resources"
    
    def path_display(self, obj):
        return format_html('<span style="color: #ffd700; font-family: monospace;">{}</span>', obj.path)
    path_display.short_description = "Full Path"

@admin.register(ResourceType)
class ResourceTypeAdmin(admin.ModelAdmin):
    """📄 RESOURCE TYPE MANAGEMENT - Classification"""
    
    list_display = [
        'name', 
        'icon_display', 
        'resource_count_display',
        'id'
    ]
    
    search_fields = ['name']
    
    fieldsets = (
        ('📄 Resource Type', {
            'fields': ('name', 'icon'),
            'description': 'Define types of resources (Test, Quiz, Exam, Lab, etc.)'
        }),
    )
    
    def icon_display(self, obj):
        return format_html('<i class="fas {}" style="font-size: 1.2rem; color: var(--neon-purple);"></i>', obj.icon)
    icon_display.short_description = "Icon"
    
    def resource_count_display(self, obj):
        count = obj.resource_set.count()
        url = reverse('admin:resources_resource_changelist') + f'?resource_type__id__exact={obj.id}'
        return format_html('<a href="{}">{} Resources</a>', url, count)
    resource_count_display.short_description = "📄 Total"

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """📎 RESOURCE/FILE MANAGEMENT - Bottom Level"""
    
    list_display = [
        'title', 
        'resource_type',
        'course_link',
        'module_link',
        'year_level_display', 
        'academic_year',
        'downloads', 
        'file_link',
        'uploaded_at'
    ]
    
    list_filter = [
        'course__university', 
        'course', 
        'resource_type', 
        'year_level', 
        'academic_year', 
        'semester',
        'uploaded_at'
    ]
    
    search_fields = ['title', 'description']
    autocomplete_fields = ['university', 'course', 'module', 'resource_type', 'uploaded_by']
    readonly_fields = ['file_size', 'downloads', 'uploaded_at', 'file_preview']
    list_editable = ['academic_year']
    list_per_page = 25
    
    fieldsets = (
        ('📎 Resource Details', {
            'fields': ('title', 'description', 'resource_type', 'file', 'file_preview'),
            'description': 'Basic resource information'
        }),
        ('📍 Location', {
            'fields': ('university', 'course', 'module'),
            'description': 'Where this resource belongs'
        }),
        ('📅 Academic Info', {
            'fields': ('year_level', 'academic_year', 'semester'),
            'description': 'Year level and academic period'
        }),
        ('📊 Metadata', {
            'fields': ('file_size', 'downloads', 'uploaded_by', 'uploaded_at'),
            'classes': ('collapse',),
        }),
    )
    
    def course_link(self, obj):
        if obj.course:
            url = reverse('admin:resources_course_change', args=[obj.course.id])
            return format_html('<a href="{}">📚 {}</a>', url, obj.course.code)
        return "—"
    course_link.short_description = "Course"
    course_link.admin_order_field = 'course__code'
    
    def module_link(self, obj):
        if obj.module:
            url = reverse('admin:resources_module_change', args=[obj.module.id])
            return format_html('<a href="{}">📁 {}</a>', url, obj.module.name)
        return "—"
    module_link.short_description = "Module"
    
    def year_level_display(self, obj):
        colors = {1: '#4CAF50', 2: '#2196F3', 3: '#FF9800', 4: '#9C27B0', 5: '#F44336'}
        names = dict(Resource.YEAR_LEVELS)
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 20px; font-size: 0.85rem;">{}</span>',
            colors.get(obj.year_level, '#666'),
            names.get(obj.year_level, f'Year {obj.year_level}')
        )
    year_level_display.short_description = "Year Level"
    year_level_display.admin_order_field = 'year_level'
    
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank" style="background: #4CAF50; color: white; padding: 5px 10px; border-radius: 5px; text-decoration: none;">📄 View</a>', obj.file.url)
        return "No file"
    file_link.short_description = "File"
    
    def file_preview(self, obj):
        if obj.file:
            return format_html(
                '<div style="margin-top: 10px;"><a href="{}" target="_blank" class="button" style="background: #667eea;">📄 Open File</a>',
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
    """📊 DOWNLOAD TRACKING - Analytics"""
    
    list_display = [
        'resource_link',
        'user_link',
        'downloaded_at',
        'ip_address'
    ]
    
    list_filter = ['downloaded_at']
    readonly_fields = ['downloaded_at']
    list_per_page = 50
    
    fieldsets = (
        ('📊 Download Information', {
            'fields': ('resource', 'user', 'downloaded_at', 'ip_address'),
        }),
    )
    
    def resource_link(self, obj):
        url = reverse('admin:resources_resource_change', args=[obj.resource.id])
        return format_html('<a href="{}">{}</a>', url, obj.resource.title)
    resource_link.short_description = "Resource"
    
    def user_link(self, obj):
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return "Anonymous"
    user_link.short_description = "User"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False