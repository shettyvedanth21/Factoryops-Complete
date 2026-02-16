FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Using python to run the bootstrapper script which launches Streamlit as a subprocess
CMD ["python", "main.py"]
