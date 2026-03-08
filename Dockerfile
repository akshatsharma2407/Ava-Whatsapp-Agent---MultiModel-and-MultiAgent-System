# 1. Use the official Python image (slim version to keep it lightweight)
FROM python:3.12-slim-bookworm

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Tell Python to print logs immediately
ENV PYTHONUNBUFFERED=1

# 4. Solves your Import Error: Tells Python where your 'ai_companion' package starts
ENV PYTHONPATH="/app"

# 5. Install system tools needed for building complex Python libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 6. Copy ONLY your requirements file first
COPY requirements.txt /app/

# 7. Install your Python packages
# MODIFICATION 1: Added --default-timeout=1000 to stop network drops.
# MODIFICATION 2: Added the CPU-only index for PyTorch. 
RUN pip install --default-timeout=1000 --no-cache-dir \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r requirements.txt

RUN  pip install pydantic[email]

# 8. Copy your actual code into the container
COPY src/ /app/

# 9. Create a protected folder for saved data
VOLUME ["/app/data"]

# 10. Document the port being used
EXPOSE 8080

# 11. Start the FastAPI server using Uvicorn
CMD ["uvicorn", "ai_companion.interfaces.webhook_endpoint:app", "--host", "0.0.0.0", "--port", "8080"]