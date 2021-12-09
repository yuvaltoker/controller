FROM python:3.8-slim-buster

RUN pip install pika
RUN pip install minio
RUN pip install pymongo
WORKDIR /app
ADD controller.py /app 
ADD controller_lib.py /app
ADD simple_json.json /app
RUN chmod +x /app/controller.py
RUN chmod +x /app/controller_lib.py
ADD wait /app
RUN chmod +x /app/wait
CMD /app/wait && ./controller.py