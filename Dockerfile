FROM python:3-slim

WORKDIR /opt/gradescope-ics

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .
COPY main.py .
COPY templates templates
COPY pyscope pyscope

EXPOSE 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]