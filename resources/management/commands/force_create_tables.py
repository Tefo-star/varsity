from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Force create all resources tables'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Create University table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resources_university (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    code VARCHAR(20) UNIQUE NOT NULL,
                    logo VARCHAR(100),
                    description TEXT,
                    created_at TIMESTAMP NOT NULL
                );
            """)
            self.stdout.write(self.style.SUCCESS('✅ Created resources_university table'))

            # Create Course table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resources_course (
                    id SERIAL PRIMARY KEY,
                    university_id INTEGER REFERENCES resources_university(id) ON DELETE CASCADE,
                    code VARCHAR(20) NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP NOT NULL,
                    UNIQUE(university_id, code)
                );
            """)
            self.stdout.write(self.style.SUCCESS('✅ Created resources_course table'))

            # Create ResourceType table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resources_resourcetype (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) NOT NULL,
                    icon VARCHAR(50) DEFAULT 'fa-file-pdf'
                );
            """)
            self.stdout.write(self.style.SUCCESS('✅ Created resources_resourcetype table'))

            # Create Module table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resources_module (
                    id SERIAL PRIMARY KEY,
                    course_id INTEGER REFERENCES resources_course(id) ON DELETE CASCADE,
                    parent_module_id INTEGER REFERENCES resources_module(id) ON DELETE CASCADE,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    "order" INTEGER DEFAULT 0,
                    created_at TIMESTAMP NOT NULL
                );
            """)
            self.stdout.write(self.style.SUCCESS('✅ Created resources_module table'))

            # Create Resource table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resources_resource (
                    id SERIAL PRIMARY KEY,
                    university_id INTEGER REFERENCES resources_university(id) ON DELETE CASCADE,
                    course_id INTEGER REFERENCES resources_course(id) ON DELETE CASCADE,
                    module_id INTEGER REFERENCES resources_module(id) ON DELETE CASCADE,
                    resource_type_id INTEGER REFERENCES resources_resourcetype(id) ON DELETE CASCADE,
                    title VARCHAR(200) NOT NULL,
                    description TEXT,
                    year INTEGER NOT NULL,
                    semester INTEGER DEFAULT 1,
                    file VARCHAR(100) NOT NULL,
                    file_size INTEGER DEFAULT 0,
                    uploaded_by_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
                    uploaded_at TIMESTAMP NOT NULL,
                    downloads INTEGER DEFAULT 0
                );
            """)
            self.stdout.write(self.style.SUCCESS('✅ Created resources_resource table'))

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS resources_r_university_course_year_idx ON resources_resource(university_id, course_id, year);")
            cursor.execute("CREATE INDEX IF NOT EXISTS resources_r_year_idx ON resources_resource(year DESC);")
            self.stdout.write(self.style.SUCCESS('✅ Created indexes'))

            # Create ResourceDownload table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resources_resourcedownload (
                    id SERIAL PRIMARY KEY,
                    resource_id INTEGER REFERENCES resources_resource(id) ON DELETE CASCADE,
                    user_id INTEGER REFERENCES auth_user(id) ON DELETE SET NULL,
                    downloaded_at TIMESTAMP NOT NULL,
                    ip_address INET
                );
            """)
            self.stdout.write(self.style.SUCCESS('✅ Created resources_resourcedownload table'))

        self.stdout.write(self.style.SUCCESS('\n🎉 All resources tables created successfully!'))