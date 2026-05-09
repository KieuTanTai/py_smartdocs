FROM python:3.14
WORKDIR /app

ENV PYTHONONLYWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir shiny httpx

COPY index.py /app/index.py
COPY assets /app/assets

EXPOSE 8052

CMD [ "shiny", "run", "index.py", "--server.address=0.0.0.0", "--server.port=8052" ]