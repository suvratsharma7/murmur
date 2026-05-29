# Murmur — L4 Instance Runbook

This document covers provisioning, connecting to, and operating the GPU inference servers that power Murmur's real-time voice pipeline. All five servers colocate on a single **Jarvis Labs NVIDIA L4** (24 GB VRAM).

---

## 1. VRAM Budget

| Service | Model | VRAM | Port |
|---|---|---|---|
| Whisper STT | `faster-whisper large-v3-turbo` (float16) | ~3 GB | 9000 |
| Kokoro TTS | `hexgrad/Kokoro-82M` | ~0.5 GB | 9001 |
| vLLM | `Qwen/Qwen2.5-7B-Instruct` (BF16, `--gpu-mem-util 0.65`) | ~15.6 GB | 8001 |
| SGLang | same model, same mem fraction | ~15.6 GB | 8002 |
| Ollama | `qwen2.5:7b-instruct` (Q4_K_M, ~5 GB) | ~5 GB | 8003 |
| **Total (worst case)** | Whisper + Kokoro + vLLM/SGLang | **~19.1 GB** | |
| **Buffer** | | **~4.9 GB** | |

Only **one** LLM server runs at a time. Whisper and Kokoro stay up across LLM swaps.

---

## 2. Provisioning an L4 on Jarvis Labs

1. Log in at [jarvislabs.ai](https://jarvislabs.ai/).
2. Click **Create Instance**.
3. Select:
   - **GPU:** NVIDIA L4
   - **Count:** 1
   - **OS:** Ubuntu 22.04 (or the default PyTorch image for pre-installed CUDA)
   - **Storage:** 80 GB SSD minimum (models are ~15 GB total; leave room for packages and logs)
4. Enable **SSH access**.
5. Click **Create**. Wait ~2 minutes for the instance to provision.
6. Note the **SSH command** shown in the dashboard — you'll use it to connect.

> **Cost:** ~₹42.5/hr (₹41.31 compute + ₹1.13 storage). Budget for ~37 hours on ₹1600 credits. Shut down promptly when not in use.

*(Screenshot placeholder: Jarvis Labs dashboard showing L4 instance creation)*

---

## 3. Connecting to the Instance

### Direct SSH

```bash
ssh -p <PORT> <USER>@<HOST>
```

Use the exact command from the Jarvis Labs dashboard.

### Exposing Ports (for Emergent orchestrator to reach the L4)

The orchestrator (running on Emergent) needs HTTP access to ports 8001-8003, 9000, and 9001 on the L4.

**Option A: Jarvis Labs built-in proxy URLs**
Jarvis Labs provides public proxy URLs for exposed ports. Check the instance dashboard for port-forwarding options.

**Option B: Cloudflare Tunnel**

```bash
# On the L4 instance:
curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# Quick tunnel (no Cloudflare account needed for testing):
cloudflared tunnel --url http://localhost:9000
# Note the generated *.trycloudflare.com URL
```

Repeat for each port, or use a `config.yml` mapping multiple subdomains.

**Option C: SSH port forwarding** (simplest for development)

```bash
# From your local machine:
ssh -p <PORT> -L 9000:localhost:9000 -L 9001:localhost:9001 -L 8001:localhost:8001 <USER>@<HOST>
```

---

## 4. Initial Setup

After SSH-ing in:

```bash
# Update system
sudo apt update && sudo apt install -y tmux lsof

# Clone the repo
git clone https://github.com/YOUR_USERNAME/murmur.git
cd murmur

# Create a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip

# Make scripts executable
chmod +x orchestrator/scripts/*.sh
```

---

## 5. Startup Order

Start services in this exact order to claim VRAM predictably:

### Step 1: Whisper STT (reserves ~3 GB)

```bash
cd ~/murmur
source .venv/bin/activate
./orchestrator/scripts/serve_whisper.sh
```

Wait for: `READY: Whisper on http://0.0.0.0:9000`

Verify:
```bash
curl http://localhost:9000/health
# {"status":"ok","model":"large-v3-turbo","compute_type":"float16"}
```

### Step 2: Kokoro TTS (reserves ~0.5 GB)

```bash
./orchestrator/scripts/serve_kokoro.sh
```

Wait for: `READY: Kokoro TTS on http://0.0.0.0:9001`

Verify:
```bash
curl http://localhost:9001/health
# {"status":"ok","model":"hexgrad/Kokoro-82M","output_sample_rate":24000}
```

### Step 3: One LLM Server

Start **one** of the following:

```bash
# vLLM (recommended first)
./orchestrator/scripts/serve_vllm.sh
# Wait for: READY: vLLM on http://0.0.0.0:8001

# OR SGLang
./orchestrator/scripts/serve_sglang.sh
# Wait for: READY: SGLang on http://0.0.0.0:8002

# OR Ollama
./orchestrator/scripts/serve_ollama.sh
# Wait for: READY: Ollama on http://0.0.0.0:8003
```

Verify (example for vLLM):
```bash
curl http://localhost:8001/v1/models
# Should list Qwen/Qwen2.5-7B-Instruct
```

---

## 6. Switching LLM Runtimes

Whisper and Kokoro stay running. Only the LLM server is swapped.

```bash
# 1. Kill the current LLM server
tmux kill-session -t murmur_vllm    # or murmur_sglang or murmur_ollama

# 2. Verify GPU memory is freed
nvidia-smi
# The LLM's ~15 GB should be released. Whisper + Kokoro remain.

# 3. Wait a few seconds for cleanup
sleep 5

# 4. Start the next runtime
./orchestrator/scripts/serve_sglang.sh
# Wait for READY line
```

---

## 7. Reading Logs

Each server runs in a named tmux session:

| Session | Service |
|---|---|
| `murmur_whisper` | Whisper STT |
| `murmur_kokoro` | Kokoro TTS |
| `murmur_vllm` | vLLM |
| `murmur_sglang` | SGLang |
| `murmur_ollama` | Ollama |

```bash
# Attach to a session to see live logs
tmux attach -t murmur_vllm

# Detach without stopping: Ctrl+b, then d

# List all active sessions
tmux ls
```

---

## 8. Health Checks (Quick)

Run any script with `--health-check` to verify without starting a new instance:

```bash
./orchestrator/scripts/serve_whisper.sh --health-check
./orchestrator/scripts/serve_kokoro.sh --health-check
./orchestrator/scripts/serve_vllm.sh --health-check
```

---

## 9. Common Failures and Remediation

### Port Already in Use

```bash
lsof -i :9000
# Identify the PID, then:
kill <PID>
# Or if it's a stale tmux session:
tmux kill-session -t murmur_whisper
```

### CUDA Out of Memory (OOM)

**Symptoms:** Server crashes during model load or first inference.

**Remediation:**
1. Verify only one LLM server is running: `tmux ls`
2. Check actual VRAM usage: `nvidia-smi`
3. Kill any unexpected GPU processes
4. If vLLM/SGLang OOMs, reduce `--gpu-memory-utilization` / `--mem-fraction-static` to `0.55` in the script
5. If Whisper OOMs during transcription of long audio, split input or reduce beam size

### Model Download Stuck or Fails

**Cause:** Network issues or Hugging Face rate limits.

```bash
# Log in to Hugging Face if the model requires auth
pip install huggingface-hub
huggingface-cli login

# Retry the script — downloads are cached, so partial progress is kept
```

### vLLM Takes Very Long to Start

vLLM compiles CUDA kernels on first run. This can take 5-10 minutes on cold start. Subsequent starts are cached.

### Kokoro Import Errors

The `kokoro` package has specific dependency requirements. If import fails:

```bash
pip install kokoro --force-reinstall
pip install soundfile  # Often needed as an implicit dependency
```

---

## 10. Stopping Everything and Cleaning Up

```bash
# Kill all Murmur tmux sessions
tmux kill-session -t murmur_whisper 2>/dev/null
tmux kill-session -t murmur_kokoro  2>/dev/null
tmux kill-session -t murmur_vllm    2>/dev/null
tmux kill-session -t murmur_sglang  2>/dev/null
tmux kill-session -t murmur_ollama  2>/dev/null

# Verify GPU is clear
nvidia-smi
# Only system processes should show VRAM usage

# Deactivate venv
deactivate
```

Then go to **Jarvis Labs dashboard** and **shut down the instance** to stop billing.

---

## 11. Issues Encountered

*(To be filled by Suvrat during actual L4 operation. Document what broke, what you tried, and what fixed it. This section is interview signal — it shows you actually ran production infrastructure.)*

---
