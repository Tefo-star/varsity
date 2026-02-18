from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.core.management import call_command
from django.conf import settings
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
    """Show year levels and modules for a course"""
    university = get_object_or_404(University, code=uni_code)
    course = get_object_or_404(Course, university=university, code=course_code)
    
    # Get year levels that have resources
    year_levels_data = []
    for level_num, level_name in Resource.YEAR_LEVELS:
        resource_count = Resource.objects.filter(course=course, year_level=level_num).count()
        if resource_count > 0:
            year_levels_data.append({
                'level': level_num,
                'name': level_name,
                'resource_count': resource_count,
            })
    
    # Get top-level modules
    modules = course.modules.filter(parent_module=None)
    
    context = {
        'university': university,
        'course': course,
        'year_levels': year_levels_data,
        'modules': modules,
    }
    return render(request, 'resources/course_detail.html', context)

def year_level_detail(request, uni_code, course_code, year_level):
    """Show academic years and modules for a specific year level"""
    university = get_object_or_404(University, code=uni_code)
    course = get_object_or_404(Course, university=university, code=course_code)
    
    # Get year level name
    year_level_dict = dict(Resource.YEAR_LEVELS)
    year_level_name = year_level_dict.get(year_level, f'Year {year_level}')
    
    # Get resources for this year level
    resources = Resource.objects.filter(course=course, year_level=year_level)
    
    # Get unique academic years
    academic_years = resources.values_list('academic_year', flat=True).distinct().order_by('-academic_year')
    
    # Get modules that have resources in this year level
    modules = Module.objects.filter(resource__in=resources).distinct()
    
    context = {
        'university': university,
        'course': course,
        'year_level': year_level,
        'year_level_name': year_level_name,
        'resources': resources,
        'academic_years': academic_years,
        'modules': modules,
    }
    return render(request, 'resources/year_level_detail.html', context)

def year_level_academic_detail(request, uni_code, course_code, year_level, academic_year):
    """Show resources for a specific year level and academic year"""
    university = get_object_or_404(University, code=uni_code)
    course = get_object_or_404(Course, university=university, code=course_code)
    
    year_level_dict = dict(Resource.YEAR_LEVELS)
    year_level_name = year_level_dict.get(year_level, f'Year {year_level}')
    
    resources = Resource.objects.filter(
        course=course, 
        year_level=year_level,
        academic_year=academic_year
    )
    
    modules = Module.objects.filter(resource__in=resources).distinct()
    
    # Group by module
    resources_by_module = {}
    for module in modules:
        module_resources = resources.filter(module=module)
        if module_resources.exists():
            resources_by_module[module] = module_resources
    
    context = {
        'university': university,
        'course': course,
        'year_level': year_level,
        'year_level_name': year_level_name,
        'academic_year': academic_year,
        'resources_by_module': resources_by_module,
    }
    return render(request, 'resources/year_level_academic_detail.html', context)

def module_detail(request, uni_code, course_code, module_id):
    """Show submodules and resources in a module"""
    university = get_object_or_404(University, code=uni_code)
    course = get_object_or_404(Course, university=university, code=course_code)
    module = get_object_or_404(Module, id=module_id, course=course)
    
    submodules = module.submodules.all()
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

def view_pdf(request, resource_id):
    """View PDF in browser"""
    resource = get_object_or_404(Resource, id=resource_id)
    return redirect(resource.file.url)

def download_resource(request, resource_id):
    """Download the file"""
    resource = get_object_or_404(Resource, id=resource_id)
    resource.downloads += 1
    resource.save()
    return redirect(resource.file.url + '?fl_attachment=true')

def run_migrations(request):
    """Run migrations manually"""
    if not settings.DEBUG:
        return HttpResponse("Not allowed", status=403)
    
    call_command('migrate')
    
    return HttpResponse("""
        <html>
            <head>
                <style>
                    body { font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #00b09b, #96c93d); color: white; padding: 50px; }
                    .container { max-width: 600px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; text-align: center; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ Migrations Run Successfully!</h1>
                    <p>All database tables have been created.</p>
                    <a href="/admin/" style="color: white;">Go to Admin →</a>
                </div>
            </body>
        </html>
    """)

def force_create_tables_view(request):
    """Force create all resources tables using management command"""
    if not settings.DEBUG:
        return HttpResponse("Not allowed", status=403)
    
    try:
        call_command('force_create_tables')
        
        return HttpResponse("""
            <html>
                <head>
                    <style>
                        body { font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #00b09b, #96c93d); color: white; padding: 50px; }
                        .container { max-width: 600px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; text-align: center; }
                        h1 { font-size: 2.5rem; margin-bottom: 20px; }
                        .success { background: rgba(0,0,0,0.2); padding: 15px; border-radius: 10px; margin: 20px 0; }
                        a { display: inline-block; background: white; color: #00b09b; padding: 15px 30px; border-radius: 50px; text-decoration: none; font-weight: bold; margin: 10px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>✅ Tables Created Successfully!</h1>
                        <div class="success">
                            <p>All resources tables have been created.</p>
                        </div>
                        <a href="/admin/">Go to Admin →</a>
                    </div>
                </body>
            </html>
        """)
    except Exception as e:
        return HttpResponse(f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #ff416c, #ff4b2b); color: white; padding: 50px; }}
                        .container {{ max-width: 600px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; text-align: center; }}
                        h1 {{ font-size: 2.5rem; margin-bottom: 20px; }}
                        .error {{ background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; margin: 20px 0; }}
                        a {{ display: inline-block; background: white; color: #ff416c; padding: 15px 30px; border-radius: 50px; text-decoration: none; font-weight: bold; margin: 10px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>❌ Error Creating Tables</h1>
                        <div class="error">
                            <p>{str(e)}</p>
                        </div>
                        <a href="/resources/run-migrations/">Try Migrations Instead</a>
                    </div>
                </body>
            </html>
        """)