from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import datetime

class University(models.Model):
    """Universities in Botswana"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True, help_text="Short code like 'ub', 'biust'")
    logo = models.ImageField(upload_to='university_logos/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('university_detail', args=[self.code])
    
    @property
    def course_count(self):
        return self.courses.count()

class Course(models.Model):
    """Courses within universities"""
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='courses')
    code = models.CharField(max_length=20, help_text="e.g., CSC101")
    name = models.CharField(max_length=200, help_text="e.g., Introduction to Programming")
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['university', 'code']
        unique_together = ['university', 'code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_absolute_url(self):
        return reverse('course_detail', args=[self.university.code, self.code])

class Module(models.Model):
    """Modules within a course (folders inside folders)"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    parent_module = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='submodules')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['course', 'order', 'name']
    
    def __str__(self):
        if self.parent_module:
            return f"{self.parent_module} > {self.name}"
        return f"{self.course.code} - {self.name}"
    
    @property
    def path(self):
        if self.parent_module:
            return f"{self.parent_module.path} > {self.name}"
        return f"{self.course.code} > {self.name}"

class ResourceType(models.Model):
    """Types: Test, Quiz, Exam, Lab, Notes, etc."""
    name = models.CharField(max_length=50)
    icon = models.CharField(max_length=50, default='fa-file-pdf')
    
    def __str__(self):
        return self.name

class Resource(models.Model):
    """Actual files (past papers, tests, etc.)"""
    SEMESTER_CHOICES = [
        (1, 'Semester 1'),
        (2, 'Semester 2'),
        (3, 'Semester 3'),
        (0, 'Full Year'),
    ]
    
    university = models.ForeignKey(University, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, blank=True, null=True)
    resource_type = models.ForeignKey(ResourceType, on_delete=models.CASCADE)
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    year = models.IntegerField(help_text="e.g., 2024")
    semester = models.IntegerField(choices=SEMESTER_CHOICES, default=1)
    
    file = models.FileField(upload_to='resources/%Y/%m/')
    file_size = models.IntegerField(default=0)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    downloads = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-year', 'course', 'resource_type']
        indexes = [
            models.Index(fields=['university', 'course', 'year']),
            models.Index(fields=['-year']),
        ]
    
    def __str__(self):
        return f"{self.course.code} - {self.title} ({self.year})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.cleanup_old_years()
    
    @classmethod
    def cleanup_old_years(cls):
        current_year = datetime.now().year
        allowed_years = [current_year, current_year-1, current_year-2]
        cls.objects.exclude(year__in=allowed_years).delete()

class ResourceDownload(models.Model):
    """Track downloads"""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)