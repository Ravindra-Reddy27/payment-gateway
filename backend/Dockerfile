# backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose the port the API runs on
EXPOSE 8000

# Set the python path so it finds your modules
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Command to start the API
# NOTE: Ensure 'src/app.py' is the correct path to your main API file.
CMD ["python", "src/app.py"]