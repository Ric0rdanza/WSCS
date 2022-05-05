FROM python:3.9.7
WORKDIR = /Project

COPY requirements.txt ./
RUN pip3 install -r requirements.txt

COPY . .

CMD ["gunicorn", "authorization:app", "-c", "gunicorn.conf.py"]
