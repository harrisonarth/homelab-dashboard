FROM python:3.12-slim
WORKDIR /app
COPY agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY core/ ./core/
COPY agent/main.py ./agent/main.py
ENV AGENT_TOKEN=""
ENV AGENT_PORT=8001
EXPOSE 8001
CMD ["sh", "-c", "uvicorn agent.main:app --host 0.0.0.0 --port ${AGENT_PORT}"]
