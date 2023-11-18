FROM python:3.11-slim-bullseye
WORKDIR /app
COPY requirements.txt /src/
RUN pip install -r /src/requirements.txt
COPY spotify_monitor.py /src
CMD ["python3", "/src/spotify_monitor.py"]
