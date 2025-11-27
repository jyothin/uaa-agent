FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN adduser --disabled-password --gecos "" deployment_user

COPY . .

RUN chown -R deployment_user:deployment_user /app

USER deployment_user

ENV PATH="/home/deployment_user/.local/bin:$PATH"
ENV PORT=8000

EXPOSE 8000

CMD ["python", "agent.py"]