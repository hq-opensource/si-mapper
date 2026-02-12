FROM python:3.12-slim-bookworm

WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .

# Expose the port
EXPOSE 8001

# Run the application
CMD ["python", "main.py"]
