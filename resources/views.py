from django.shortcuts import render, get_object_or_404
from .models import University, Course

def resources_dashboard(request):
    """Main resources page - list all universities"""
    universities = University.objects.all()
    context = {
        'universities': universities,
    }
    return render(request, 'resources/dashboard.html', context)

def university_detail(request, uni_code):
    """Show courses for a specific university"""
    university = get_object_or_404(University, code=uni_code)
    courses = university.courses.all()
    context = {
        'university': university,
        'courses': courses,
    }
    return render(request, 'resources/university_detail.html', context)

def course_detail(request, uni_code, course_code):
    """Show details for a specific course"""
    university = get_object_or_404(University, code=uni_code)
    course = get_object_or_404(Course, university=university, code=course_code)
    context = {
        'university': university,
        'course': course,
    }
    return render(request, 'resources/course_detail.html', context)