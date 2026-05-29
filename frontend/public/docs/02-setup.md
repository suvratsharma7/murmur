# Setup Guide

This guide covers installation, configuration, and deployment of MURMUR.

## Prerequisites

### Required

- **Python 3.11+** - Backend runtime
- **Node.js 18+ / Yarn** - Frontend build tools
- **MongoDB** - Metrics persistence (local or Atlas)

### Optional

- **Jarvis Labs L4 GPU instance** - For real inference (not required for mock mode)
- **Docker** - Container deployment (optional)

## Quick Start (Mock Mode)

The fastest way to run MURMUR without GPU infrastructure:

### 1. Clone Repository

```bash
git clone <repository-url>
cd murmur
```

### 2. Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env
MURMUR_RUNTIME=mock
MONGO_URL=mongodb://localhost:27017
DB_NAME=murmur_dev
CORS_ORIGINS=*
```

### 4. Start MongoDB (if local)

```bash
# macOS (via Homebrew)
brew services start mongodb-community

# Linux (systemd)
sudo systemctl start mongod

# Docker
docker run -d -p 27017:27017 --name mongo mongo:7
```

### 5. Start Backend

```bash
# Development mode with auto-reload
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

Backend will be available at `http://localhost:8001`

### 6. Frontend Setup

```bash
cd frontend
yarn install
```

### 7. Configure Frontend Environment

```bash
# frontend/.env
REACT_APP_BACKEND_URL=http://localhost:8001
```

### 8. Start Frontend

```bash
yarn dev
```

Frontend will be available at `http://localhost:3000`

### 9. Test the Application

1. Navigate to `http://localhost:3000/demo`
2. Ensure runtime selector shows "mock"
3. Hold push-to-talk button and speak
4. Verify transcript appears and metrics update

## Production Setup (Real GPU)

### GPU Server Setup (Jarvis Labs L4)

1. **Provision L4 Instance**
   ```bash
   # Recommended specs
   GPU: 1x L4 (24GB VRAM)
   CPU: 8+ cores
   RAM: 32GB+
   Storage: 100GB+ SSD
   ```

2. **Install Dependencies**
   ```bash
   # CUDA 12.1+
   # PyTorch 2.0+
   # vLLM, SGLang, Ollama
   # Whisper, Kokoro TTS
   ```

3. **Run Server Startup Scripts**
   ```bash
   cd orchestrator/scripts
   
   # Start Whisper STT
   bash serve_whisper.sh --health-check
   
   # Start Kokoro TTS
   bash serve_kokoro.sh --health-check
   
   # Start LLM runtime (choose one or all)
   bash serve_vllm.sh --health-check
   bash serve_sglang.sh --health-check
   bash serve_ollama.sh --health-check
   ```

   See [05-runbook.md](05-runbook.md) for detailed server deployment.

4. **Get GPU Server IP**
   ```bash
   curl ifconfig.me
   # Example: 203.0.113.42
   ```

### Orchestrator Configuration

Update backend/.env with GPU server URLs:

```bash
MURMUR_RUNTIME=vllm  # or sglang, ollama
MONGO_URL=mongodb://localhost:27017
DB_NAME=murmur_prod
CORS_ORIGINS=https://yourdomain.com

# GPU service URLs
STT_URL=http://203.0.113.42:9000
TTS_URL=http://203.0.113.42:9001
VLLM_URL=http://203.0.113.42:8001
SGLANG_URL=http://203.0.113.42:8002
OLLAMA_URL=http://203.0.113.42:8003
```

### Frontend Configuration

```bash
# frontend/.env
REACT_APP_BACKEND_URL=https://api.yourdomain.com
```

### Process Management

Use Supervisor for production:

```bash
# Install supervisor
sudo apt-get install supervisor

# Copy config
sudo cp deployment/supervisord.conf /etc/supervisor/conf.d/murmur.conf

# Start services
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all

# Check status
sudo supervisorctl status
```

## Docker Deployment (Optional)

### Build Images

```bash
# Backend
docker build -t murmur-backend ./backend

# Frontend
docker build -t murmur-frontend ./frontend
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  mongodb:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo-data:/data/db

  backend:
    image: murmur-backend
    ports:
      - "8001:8001"
    environment:
      - MURMUR_RUNTIME=mock
      - MONGO_URL=mongodb://mongodb:27017
    depends_on:
      - mongodb

  frontend:
    image: murmur-frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:8001
    depends_on:
      - backend

volumes:
  mongo-data:
```

```bash
docker-compose up -d
```

## Environment Variables Reference

### Backend (.env)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MURMUR_RUNTIME` | Yes | `mock` | LLM runtime: vllm, sglang, ollama, mock |
| `MONGO_URL` | Yes | - | MongoDB connection string |
| `DB_NAME` | Yes | `murmur_dev` | Database name |
| `CORS_ORIGINS` | No | `*` | CORS allowed origins (comma-separated) |
| `STT_URL` | If real | - | Whisper STT service URL |
| `TTS_URL` | If real | - | Kokoro TTS service URL |
| `VLLM_URL` | If real | - | vLLM service URL |
| `SGLANG_URL` | If real | - | SGLang service URL |
| `OLLAMA_URL` | If real | - | Ollama service URL |

### Frontend (.env)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REACT_APP_BACKEND_URL` | Yes | `http://localhost:8001` | Backend API base URL |

## Verification

### Health Checks

```bash
# Backend health
curl http://localhost:8001/api/healthz

# Expected response
{
  "status": "healthy",
  "runtime": "mock",
  "services": {
    "stt": "healthy",
    "tts": "healthy",
    "llm": "healthy"
  }
}
```

### Runtime List

```bash
curl http://localhost:8001/api/runtimes

# Expected response
{
  "runtimes": [
    {"name": "mock", "healthy": true},
    {"name": "vllm", "healthy": false},
    {"name": "sglang", "healthy": false},
    {"name": "ollama", "healthy": false}
  ]
}
```

### WebSocket Test

```bash
# Install websocat
brew install websocat  # macOS
# or download from https://github.com/vi/websocat

# Connect to WebSocket
websocat ws://localhost:8001/api/ws/stream?runtime=mock

# Send message (in JSON format)
{"type": "audio_start"}
```

## Troubleshooting

### Backend won't start

```bash
# Check Python version
python --version  # Must be 3.11+

# Verify dependencies
pip list | grep fastapi

# Check MongoDB connection
mongosh $MONGO_URL
```

### Frontend build fails

```bash
# Clear cache
rm -rf node_modules .next
yarn install
yarn build
```

### WebSocket connection fails

```bash
# Check CORS settings
# backend/.env: CORS_ORIGINS=http://localhost:3000

# Verify backend is accessible
curl http://localhost:8001/api/healthz

# Check browser console for errors
```

### Mock mode not working

```bash
# Verify environment
grep MURMUR_RUNTIME backend/.env  # Should be 'mock'

# Restart backend
supervisorctl restart backend
# or kill and restart uvicorn
```

### GPU services unreachable

```bash
# Test connectivity
curl http://GPU_IP:9000/health  # Whisper
curl http://GPU_IP:9001/health  # Kokoro
curl http://GPU_IP:8001/v1/models  # vLLM

# Check firewall
sudo ufw status
# Ensure ports 8001-8003, 9000-9001 are open

# Check GPU server logs
tmux attach -t whisper
tmux attach -t vllm
```

## Performance Tuning

### Backend

```bash
# Increase workers for production
uvicorn server:app --host 0.0.0.0 --port 8001 --workers 4

# Use gunicorn with uvicorn workers
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8001
```

### MongoDB

```python
# Index for query performance
db.turns.createIndex({"timestamp": -1})
db.turns.createIndex({"runtime": 1, "timestamp": -1})
```

### Frontend

```bash
# Production build optimization
yarn build

# Serve with compression
npx serve -s build -l 3000
```

## Next Steps

- [API Reference](04-api.md) - REST and WebSocket API documentation
- [Runtime Abstraction](03-runtime-abstraction.md) - Adding custom runtimes
- [Benchmarks](07-benchmarks.md) - Running performance benchmarks

---

**Previous:** [← Introduction](01-intro.md) | **Next:** [Runtime Abstraction →](03-runtime-abstraction.md)
