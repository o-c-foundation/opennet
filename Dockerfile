FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install flask requests ecdsa cryptography
EXPOSE 8000
CMD ["python", "opennet_node_service.py"]
