FROM python:3.11

# Install dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Run collectstatic if needed
RUN python manage.py collectstatic --noinput

# Expose port and run app
EXPOSE 8000
CMD ["gunicorn", "aiservice.wsgi:application", "--bind", "0.0.0.0:8000"]
