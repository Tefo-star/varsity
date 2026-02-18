from django.shortcuts import render, get_object_or_404
from .models import University, Course, Module, Resource, ResourceType

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
    """Show modules and years for a course"""
    university = get_object_or_404(University, code=uni_code)
    course = get_object_or_404(Course, university=university, code=course_code)
    
    # Get top-level modules (folders)
    modules = course.modules.filter(parent_module=None)
    
    # Get unique years from resources
    years = Resource.objects.filter(course=course).values_list('year', flat=True).distinct().order_by('-year')
    
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
    
    # Get resources in this module grouped by type
    resources = Resource.objects.filter(module=module)
    resource_types = ResourceType.objects.all()
    
    resources_by_type = {}
    for rtype in resource_types:
        resources_by_type[rtype.name] = resources.filter(resource_type=rtype)
    
    context = {
        'university': university,
        'course': course,
        'module': module,
        'submodules': submodules,
        'resources_by_type': resources_by_type,
    }
    return render(request, 'resources/module_detail.html', context)

def year_detail(request, uni_code, course_code, year):
    """Show all resources for a specific year"""
    university = get_object_or_404(University, code=uni_code)
    course = get_object_or_404(Course, university=university, code=course_code)
    
    resources = Resource.objects.filter(course=course, year=year)
    
    # Group by module and then by type
    modules = Module.objects.filter(course=course)
    
    context = {
        'university': university,
        'course': course,
        'year': year,
        'resources': resources,
        'modules': modules,
    }
    return render(request, 'resources/year_detail.html', context)

def view_pdf(request, resource_id):
    """View PDF in browser"""
    resource = get_object_or_404(Resource, id=resource_id)
    # Increment view count if you want
    return redirect(resource.file.url)  # Cloudinary handles PDF viewing

def download_resource(request, resource_id):
    """Download the file"""
    resource = get_object_or_404(Resource, id=resource_id)
    resource.downloads += 1
    resource.save()
    return redirect(resource.file.url + '?fl_attachment=true')  # Force download