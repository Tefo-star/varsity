from django.shortcuts import render

def resources_dashboard(request):
    return render(request, 'resources/dashboard.html')