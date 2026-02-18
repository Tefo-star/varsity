def run_migrations(request):
    if not settings.DEBUG:
        return HttpResponse("Not allowed", status=403)
    
    # Run ALL migrations, not just resources
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
                    <h1>✅ All Migrations Run Successfully!</h1>
                    <p>All database tables have been created.</p>
                    <a href="/admin/" style="color: white;">Go to Admin →</a>
                </div>
            </body>
        </html>
    """)