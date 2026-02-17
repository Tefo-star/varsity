from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q
from .models import University, Course, Module, Resource, ResourceType
from .forms import ResourceUploadForm
import os

def resources_dashboard(request):
    """Main resources page - shows all universities"""
    universities = University.objects.annotate(
        resource_count=Count('courses__resource')
    )
    
    # Get available years
    current_year = timezone.now().year
    available_years = [current_year, current_year-1, current_year-2]
    
    context = {
        'universities': universities,
        'available_years': available_years,
        'total_resources': Resource.objects.count(),
    }
    return render(request, 'resources/dashboard.html', context)

def university_detail(request, uni_code):
    """Show courses for a specific university"""
    university = get_object_or_404(University, code=uni_code)
    courses = university.courses.annotate(
        resource_count=Count('resource')
    ).filter(resource_count__gt=0)
    
    # Get resource counts by year
    current_year = timezone.now().year
    years = []
    for year in [current_year, current_year-1, current_year-2]:
        count = Resource.objects.filter(
            course__university=university,
            year=year
        ).count()
        if count > 0:
            years.append({'year': year, 'count': count})
    
    context = {
        'university': university,
        'courses': courses,
        'years': years,
    }
    return render(request, 'resources/university_detail.html', context)

def course_detail(request, uni_code, course_code):
    """Show modules and years for a course"""
    university = get_object_or_404(University, code=uni_code)
    course = get_object_or_404(Course, university=university, code=course_code)
    
    # Get modules
    modules = course.modules.filter(parent_module=None)  # Top-level modules
    
    # Get years with resources
    current_year = timezone.now().year
    years = []
    for year in [current_year, current_year-1, current_year-2]:
        resources = Resource.objects.filter(course=course, year=year)
        if resources.exists():
            # Group by resource type
            by_type = resources.values('resource_type__name', 'resource_type__icon').annotate(
                count=Count('id')
            )
            years.append({
                'year': year,
                'resources': resources,
                'by_type': by_type,
                'total': resources.count()
            })
    
    context = {
        'university': university,
        'course': course,
        'modules': modules,
        'years': years,
    }
    return render(request, 'resources/course_detail.html', context)

def module_detail(request, uni_code, course_code, module_id):
    """Show submodules and resources in a module"""
    university = get_object_or_404(University, code=uni_code)
    course = get_object_or_404(Course, university=university, code=course_code)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    # Get submodules
    submodules = module.submodules.all()
    
    # Get resources in this module
    resources = Resource.objects.filter(module=module)
    
    context = {
        'university': university,
        'course': course,
        'module': module,
        'submodules': submodules,
        'resources': resources,
    }
    return render(request, 'resources/module_detail.html', context)

def year_view(request, uni_code, course_code, year):
    """Show all resources for a specific year"""
    university = get_object_or_404(University, code=uni_code)
    course = get_object_or_404(Course, university=university, code=course_code)
    
    resources = Resource.objects.filter(course=course, year=year)
    
    # Group by resource type
    by_type = {}
    for resource in resources:
        type_name = resource.resource_type.name
        if type_name not in by_type:
            by_type[type_name] = []
        by_type[type_name].append(resource)
    
    context = {
        'university': university,
        'course': course,
        'year': year,
        'by_type': by_type,
    }
    return render(request, 'resources/year_detail.html', context)

@login_required
def upload_resource(request):
    """Upload new resource with folder selection"""
    if request.method == 'POST':
        form = ResourceUploadForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.uploaded_by = request.user
            resource.file_size = request.FILES['file'].size
            
            # Auto-delete oldest year logic is in model save()
            resource.save()
            
            messages.success(request, 'Resource uploaded successfully! 📚')
            return redirect('resources_dashboard')
    else:
        form = ResourceUploadForm()
    
    # Get available years for dropdown
    current_year = timezone.now().year
    years = [current_year, current_year-1, current_year-2]
    
    context = {
        'form': form,
        'years': years,
    }
    return render(request, 'resources/upload.html', context)

def download_resource(request, resource_id):
    """Track downloads and serve file"""
    resource = get_object_or_404(Resource, id=resource_id)
    resource.downloads += 1
    resource.save()
    
    # Optional: track download
    ResourceDownload.objects.create(
        resource=resource,
        user=request.user if request.user.is_authenticated else None,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    return redirect(resource.file.url)

# AJAX endpoints for dynamic loading (optional)
def get_modules_ajax(request):
    """API to get modules for a course (for dynamic dropdowns)"""
    course_id = request.GET.get('course_id')
    modules = Module.objects.filter(course_id=course_id).values('id', 'name', 'parent_module')
    return JsonResponse(list(modules), safe=False)