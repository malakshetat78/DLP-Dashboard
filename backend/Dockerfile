# استخدام Python 3.11 كأساس
FROM python:3.11-slim

# تعيين متغيرات البيئة
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# تثبيت المتطلبات النظامية
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# إنشاء مستخدم غير root
RUN useradd -m -u 1000 dlp_user && \
    mkdir -p /app/encrypted_storage /app/keys /app/logs && \
    chown -R dlp_user:dlp_user /app

# تعيين مجلد العمل
WORKDIR /app

# نسخ متطلبات Python
COPY requirements.txt .

# تثبيت المكتبات
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# نسخ كود التطبيق
COPY --chown=dlp_user:dlp_user . .

# التبديل للمستخدم غير root
USER dlp_user

# فتح المنفذ
EXPOSE 5000

# نقطة الدخول
ENTRYPOINT ["python"]
CMD ["app.py"]

# أو استخدام Gunicorn للإنتاج:
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]