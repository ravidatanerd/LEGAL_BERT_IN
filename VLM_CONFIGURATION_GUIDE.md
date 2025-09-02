# 🤖 Vision-Language Models (VLM) Configuration Guide

## 📋 **What are VLMs?**
Vision-Language Models extract text and understand content from PDF documents without traditional OCR. InLegalDesk supports multiple VLM options with different quality/speed tradeoffs.

---

## 🎯 **Quick Setup (Recommended)**

### **🏆 Best Quality (OpenAI First):**
```bash
# In your .env file:
VLM_ORDER=openai,donut,pix2struct,tesseract_fallback
OPENAI_API_KEY=your_api_key_here
```

### **⚡ Using Presets (Easiest):**
```bash
# Choose one preset in your .env file:
VLM_PRESET=premium      # Best quality (OpenAI only)
VLM_PRESET=high         # Balanced (OpenAI + local models)
VLM_PRESET=offline      # No API calls needed
VLM_PRESET=fast         # Prioritize speed
```

---

## 🔧 **Available VLM Models:**

| Model | Quality | Speed | Cost | Requirements |
|-------|---------|-------|------|--------------|
| **openai** | ⭐⭐⭐⭐⭐ | ⚡⚡⚡⚡ | 💰💰 | OpenAI API Key |
| **donut** | ⭐⭐⭐⭐ | ⚡⚡ | Free | GPU recommended |
| **pix2struct** | ⭐⭐⭐ | ⚡⚡ | Free | GPU recommended |
| **tesseract_fallback** | ⭐⭐ | ⚡⚡⚡⚡⚡ | Free | Always works |

---

## 🎚️ **Quality Presets Explained:**

### **🏆 PREMIUM** (`VLM_PRESET=premium`)
- **Models**: OpenAI → Tesseract fallback
- **Best for**: Highest accuracy needed
- **Requires**: OpenAI API key
- **Cost**: ~$0.01-0.02 per document page
- **Speed**: Very fast

### **⚖️ HIGH** (`VLM_PRESET=high`)
- **Models**: OpenAI → Donut → Pix2Struct → Tesseract
- **Best for**: Production use with fallbacks
- **Requires**: OpenAI API key + local models
- **Cost**: Medium (API + compute)
- **Speed**: Fast

### **⚖️ BALANCED** (`VLM_PRESET=balanced`)
- **Models**: Donut → OpenAI → Pix2Struct → Tesseract
- **Best for**: Cost-conscious with API backup
- **Requires**: Local models (GPU recommended)
- **Cost**: Low to medium
- **Speed**: Medium

### **⚡ FAST** (`VLM_PRESET=fast`)
- **Models**: Tesseract → OpenAI
- **Best for**: Speed over accuracy
- **Requires**: Basic OCR + optional API
- **Cost**: Low
- **Speed**: Very fast

### **🔒 OFFLINE** (`VLM_PRESET=offline`)
- **Models**: Donut → Pix2Struct → Tesseract
- **Best for**: No internet/API restrictions
- **Requires**: Local models only
- **Cost**: Free (compute only)
- **Speed**: Slower

### **⚡ BASIC** (`VLM_PRESET=basic`)
- **Models**: Tesseract only
- **Best for**: Simple text extraction
- **Requires**: Nothing special
- **Cost**: Free
- **Speed**: Very fast

---

## 🛠️ **Manual Configuration:**

### **Environment Variables:**
```bash
# Option 1: Use preset (easiest)
VLM_PRESET=high

# Option 2: Custom order
VLM_ORDER=openai,donut,pix2struct,tesseract_fallback

# Performance settings
VLM_BATCH_SIZE=4
VLM_TIMEOUT=300
ENABLE_OCR_FALLBACK=true
```

### **API Configuration:**
```bash
# Configure VLM via REST API
POST /vlm/config
{
    "preset": "high"
}

# Or custom order
POST /vlm/config
{
    "custom_order": ["openai", "donut", "tesseract_fallback"]
}

# Get current config
GET /vlm/config

# Get recommendations
GET /vlm/recommendations
```

---

## 🎯 **Choosing the Right Configuration:**

### **💼 For Production Legal Research:**
```bash
VLM_PRESET=high
OPENAI_API_KEY=your_key
```
- Best balance of quality and reliability
- OpenAI for complex documents, local models for backup

### **💰 For Budget-Conscious Use:**
```bash
VLM_PRESET=offline
```
- No API costs
- Good quality with local models
- Requires GPU for best performance

### **⚡ For High-Volume Processing:**
```bash
VLM_PRESET=fast
```
- Prioritizes speed
- OCR first, API backup for complex cases

### **🔒 For Air-Gapped Environments:**
```bash
VLM_PRESET=offline
```
- No internet required
- All processing local

---

## 🔍 **Model Processing Order:**

VLMs are tried in order until one succeeds:

1. **First model** attempts extraction
2. If it fails → **Second model** tries
3. Continue until success or all models tried
4. **Tesseract fallback** usually works as last resort

### **Example Flow (HIGH preset):**
```
Document → OpenAI Vision → Success ✅
                       → Fail → Donut → Success ✅
                                    → Fail → Pix2Struct → Success ✅
                                                       → Fail → Tesseract → Success ✅
```

---

## ⚙️ **Advanced Settings:**

### **Performance Tuning:**
```bash
# Batch processing
VLM_BATCH_SIZE=4        # Process 4 pages at once

# Timeout settings
VLM_TIMEOUT=300         # 5 minutes per document

# Memory management
MAX_WORKERS=4           # Parallel processing threads
```

### **Model-Specific Settings:**
```bash
# OpenAI settings
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_MAX_TOKENS=4000

# Local model settings
MODEL_DEVICE=auto       # auto, cpu, cuda
MODEL_CACHE_DIR=./models
```

---

## 🚨 **Troubleshooting:**

### **OpenAI Model Not Working:**
```bash
# Check API key
echo $OPENAI_API_KEY

# Test API access
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     https://api.openai.com/v1/models
```

### **Local Models Not Working:**
```bash
# Check transformers installation
python -c "import transformers; print('OK')"

# Check GPU availability
python -c "import torch; print(torch.cuda.is_available())"
```

### **All Models Failing:**
```bash
# Enable OCR fallback
ENABLE_OCR_FALLBACK=true

# Use basic preset
VLM_PRESET=basic
```

---

## 📊 **Performance Comparison:**

| Configuration | Accuracy | Speed | Cost/Doc | GPU Needed |
|---------------|----------|-------|----------|------------|
| **premium** | 95% | 2s | $0.02 | No |
| **high** | 90% | 5s | $0.01 | Optional |
| **balanced** | 85% | 10s | $0.005 | Yes |
| **fast** | 75% | 1s | $0.001 | No |
| **offline** | 80% | 15s | $0 | Yes |
| **basic** | 60% | 0.5s | $0 | No |

---

## 🎉 **Getting Started:**

### **1. Quick Start (OpenAI):**
```bash
# Add to .env
VLM_PRESET=premium
OPENAI_API_KEY=your_key_here

# Restart backend
python app.py
```

### **2. No-Cost Setup:**
```bash
# Add to .env
VLM_PRESET=offline

# Install local models
pip install transformers torch

# Restart backend
python app.py
```

### **3. Check Configuration:**
```bash
# Visit in browser
http://localhost:8877/vlm/config

# Or use curl
curl http://localhost:8877/vlm/recommendations
```

**🎊 Your VLM configuration is now optimized for your needs!**