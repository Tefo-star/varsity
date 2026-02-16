#!/bin/bash
echo "Installing dependencies..."
pip install -r requirements.txt

echo "Running migrations..."
python manage.py migrate

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Ensuring gunicorn is in PATH..."
# This line helps ensure the virtual environment's bin directory is in PATH
export PATH="/opt/render/project/src/.venv/bin:$PATH"

echo "Build completed successfully!"