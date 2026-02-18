#!/bin/bash
set -e  # Stop on any error

echo "========================================"
echo "🚀 Starting build process..."
echo "========================================"

echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo "🔍 Checking environment variables..."
echo "DATABASE_URL is set: ${#DATABASE_URL}"

echo "🗄️  Running database migrations..."
python manage.py migrate --noinput

echo "📂 Collecting static files..."
python manage.py collectstatic --noinput

echo "✅ Build completed successfully!"
echo "========================================"