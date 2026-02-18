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
        app_label = 'resources'
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
        app_label = 'resources'
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
        app_label = 'resources'
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
    
    class Meta:
        app_label = 'resources'
        verbose_name = 'Resource Type'
        verbose_name_plural = 'Resource Types'
    
    def __str__(self):
        return self.name

class Resource(models.Model):
    """Actual files (past papers, tests, etc.)"""
    
    YEAR_LEVELS = [
        (1, 'First Year'),
        (2, 'Second Year'),
        (3, 'Third Year'),
        (4, 'Fourth Year'),
        (5, 'Fifth Year'),
    ]
    
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
    
    # Year level (First Year, Second Year, etc.)
    year_level = models.IntegerField(choices=YEAR_LEVELS, default=1, help_text="Academic year level")
    
    # Academic calendar year
    academic_year = models.IntegerField(help_text="Calendar year e.g., 2024")
    
    semester = models.IntegerField(choices=SEMESTER_CHOICES, default=1)
    
    file = models.FileField(upload_to='resources/%Y/%m/')
    file_size = models.IntegerField(default=0)
    
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    downloads = models.IntegerField(default=0)
    
    class Meta:
        app_label = 'resources'
        ordering = ['-academic_year', 'course', 'resource_type']
        indexes = [
            models.Index(fields=['university', 'course', 'year_level', 'academic_year']),
            models.Index(fields=['-academic_year']),
        ]
        verbose_name = 'Resource'
        verbose_name_plural = 'Resources'
    
    def __str__(self):
        return f"{self.course.code} - {self.title} ({self.get_year_level_display()} {self.academic_year})"
    
    def save(self, *args, **kwargs):
        # Ensure academic_year is set
        if not self.academic_year:
            self.academic_year = datetime.now().year
        super().save(*args, **kwargs)
        self.cleanup_old_years()
    
    @classmethod
    def cleanup_old_years(cls):
        """Keep only 3 most recent academic years"""
        current_year = datetime.now().year
        allowed_years = [current_year, current_year-1, current_year-2]
        cls.objects.exclude(academic_year__in=allowed_years).delete()

class ResourceDownload(models.Model):
    """Track downloads"""
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    class Meta:
        app_label = 'resources'
        verbose_name = 'Resource Download'
        verbose_name_plural = 'Resource Downloads'