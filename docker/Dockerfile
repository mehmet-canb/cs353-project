FROM python:3.12-alpine

WORKDIR /app

COPY . .

RUN pip install -r requirements.lock

CMD ["python", "src/pms/__init__.py"]
