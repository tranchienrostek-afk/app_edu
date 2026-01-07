# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (needed for Pillow/OpenCV if extended, but good practice)
# libgl1-mesa-glx might be needed if opencv-python is ever added, 
# for now minimal build.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 5000 for the Flask app
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=server.py
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "server.py"]
