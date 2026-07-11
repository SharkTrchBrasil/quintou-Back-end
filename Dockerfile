FROM python:3.12-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o resto da aplicação
COPY . .

# Variáveis de ambiente default
ENV PORT=8000
ENV HOST=0.0.0.0

# Expôr a porta
EXPOSE 8000

# Comando para rodar a aplicação
CMD ["sh", "-c", "uvicorn app.main:app --host $HOST --port $PORT"]
