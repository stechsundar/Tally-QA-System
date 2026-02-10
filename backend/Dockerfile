FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for AI libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Hugging Face Spaces use port 7860 by default
ENV PORT=7860
EXPOSE 7860

# Run uvicorn directly instead of through python
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
