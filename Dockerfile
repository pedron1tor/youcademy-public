# Use Python 3.11.5 as the base image
FROM python:3.11.5-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user and switch to it
RUN useradd -m myuser
USER myuser

# Create and activate virtual environment
ENV VIRTUAL_ENV=/home/myuser/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install Python dependencies
COPY --chown=myuser:myuser requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy project
COPY --chown=myuser:myuser . .

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Copy the entrypoint script
COPY --chown=myuser:myuser entrypoint.sh .
RUN chmod +x entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["./entrypoint.sh"]

# Default command (can be overridden)
CMD ["run_server"]