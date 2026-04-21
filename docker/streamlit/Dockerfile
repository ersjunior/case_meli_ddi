FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

# Texto das resoluções do case para a página Streamlit "Resoluções"
COPY docs/Respostas.md /app/docs/Respostas.md

COPY serving/streamlit /app/serving/streamlit

WORKDIR /app/serving/streamlit

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
