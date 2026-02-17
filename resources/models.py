from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime

class University(models.Model):
    """Universities like UB, BUAN, BIUST, etc."""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)  # ub, buan, biust
    logo = models.ImageField(upload_to='university_logos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def total_resources(self):
        return Resource.objects.filter(course__university=self).count()

class Course(models.Model):
    """Courses like CSC101, MTH201, etc."""
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='courses')
    code = models.CharField(max_length=20)  # CSC101
    name = models.CharField(max_length=200)  # Introduction to Programming
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['university', 'code']
        unique_together = ['university', 'code']  # Prevent duplicates
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Module(models.Model):
    """Modules within a course (folders inside folders)"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    parent_module = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='submodules')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)  # For sorting
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['course', 'order', 'name']
    
    def __str__(self):
        if self.parent_module:
            return f"{self.parent_module} > {self.name}"
        return f"{self.course.code} - {self.name}"
    
    @property
    def path(self):
        """Get full folder path"""
        if self.parent_module:
            return f"{self.parent_module.path} > {self.name}"
        return f"{self.course.code} > {self.name}"

class ResourceType(models.Model):
    """Types: Test, Quiz, Exam, Lab, Notes, etc."""
    name = models.CharField(max_length=50)  # Test, Quiz, Exam, Lab, Notes
    icon = models.CharField(max_length=50, default='fa-file-pdf')  # Font Awesome icon
    
    def __str__(self):
        return self.name

class Resource(models.Model):
    """Actual files (past papers, tests, etc.)"""
    # Folder structure
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, blank=True, null=True)
    
    # Resource details
    resource_type = models.ForeignKey(ResourceType, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # Year management - only keep 3 years
    year = models.IntegerField()  # 2024, 2025, 2026
    
    # File
    file = models.FileField(upload_to='resources/%Y/%m/')
    file_size = models.IntegerField(default=0)  # In bytes
    
    # Metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    downloads = models.IntegerField(default=0)
    
    # Semester info (optional)
    SEMESTER_CHOICES = [
        (1, 'Semester 1'),
        (2, 'Semester 2'),
        (3, 'Semester 3'),
        (0, 'Full Year'),
    ]
    semester = models.IntegerField(choices=SEMESTER_CHOICES, default=1)
    
    class Meta:
        ordering = ['-year', 'course', 'resource_type']
        indexes = [
            models.Index(fields=['university', 'course', 'year']),
            models.Index(fields=['-year']),
        ]
    
    def __str__(self):
        return f"{self.course.code} - {self.title} ({self.year})"
    
    def save(self, *args, **kwargs):
        # Auto-delete oldest year when new year added
        super().save(*args, **kwargs)
        self.cleanup_old_years()
    
    @classmethod
    def cleanup_old_years(cls):
        """Keep only 3 most recent years"""
        current_year = datetime.now().year
        allowed_years = [current_year, current_year-1, current_year-2]
        
        # Delete resources older than allowed years
        cls.objects.exclude(year__in=allowed_years).delete()

class ResourceDownload(models.Model):
    """Track downloads (optional)"""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)