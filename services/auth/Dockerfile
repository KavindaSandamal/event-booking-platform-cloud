FROM python:3.11-slim
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared components (will be copied from build context)
COPY shared /app/shared

# Copy application code
COPY app ./app

# Expose port
EXPOSE 8000

# Run the enhanced application
CMD ["uvicorn","app.main_enhanced:app","--host","0.0.0.0","--port","8000","--reload"]
