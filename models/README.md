# SREE AI Engine - Model Repository & Hardware Alignment

This directory documents the local AI models supported and recommended for **Project SREE**.

## Recommended Configuration (Zero Operating Cost)

| Model | Parameters | Quantization | VRAM Required | Ideal Hardware | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`llama3.2:3b`** | 3.2 Billion | Q4_K_M | **~2.0 GB** | **NVIDIA RTX 2050 (4 GB)** | **Primary Choice**: Balanced reasoning, fast generation (40-60 tps), fits 100% in VRAM. |
| **`llama3.2:1b`** | 1.2 Billion | Q4_K_M | **~1.3 GB** | Low-RAM / Battery Saver | Ultra-fast fallback for low memory conditions. |
| **`qwen2.5:3b`** | 3.0 Billion | Q4_K_M | **~2.2 GB** | NVIDIA RTX 2050 (4 GB) | Excellent multilingual and coding performance. |

## Managing Models via Ollama CLI

```bash
# Pull model
ollama pull llama3.2:3b

# List downloaded models
ollama list

# Test interactive terminal run
ollama run llama3.2:3b

# Remove model to reclaim disk space
ollama rm <model-name>
```

All models are downloaded once and cached in `~/.ollama/models`. No internet connection is needed during conversation inference.

