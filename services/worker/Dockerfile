FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared components (will be copied from build context)
COPY shared /app/shared

# Copy application code
COPY app/ .

# Expose port
EXPOSE 8004

# Run the application
CMD ["python", "main.py"]