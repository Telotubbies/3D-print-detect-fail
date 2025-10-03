# ใช้ Python 3.10 (รองรับ Ultralytics / FastAPI ดีสุด)
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# ติดตั้ง dependencies ที่จำเป็น
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ด backend ทั้งหมด
COPY . .

# เปิดพอร์ต FastAPI
EXPOSE 8000

# รัน FastAPI ด้วย Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
