from django.db import models
from django.urls import reverse

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
        unique_together = ['university', 'code']  # Prevent duplicate course codes in same uni
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_absolute_url(self):
        return reverse('course_detail', args=[self.university.code, self.code])