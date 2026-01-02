# Fenyr AI Trading Agent

> 🤖 GPT-5.2 powered autonomous trading bot for WEEX AI Wars Hackathon

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![OpenAI GPT-5.2](https://img.shields.io/badge/OpenAI-GPT--5.2-green.svg)](https://openai.com/)
[![WEEX API](https://img.shields.io/badge/WEEX-API-orange.svg)](https://www.weex.com/)

## 🎯 Overview

Fenyr is an AI-powered trading agent that uses **GPT-5.2** to analyze market data and make autonomous trading decisions on WEEX Exchange. Built for the **AI Wars: WEEX Alpha Awakens** hackathon.

## ✨ Features

- **GPT-5.2 Analysis** - Uses latest OpenAI model for market analysis
- **Function Calling** - AI can call trading functions directly
- **Multi-Strategy** - RSI, Momentum, Funding Rate arbitrage
- **AI Log Compliance** - Automatic upload of AI reasoning to WEEX
- **Risk Management** - Position sizing, max leverage limits

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FENYR TRADING AGENT                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  GPT-5.2    │───▶│   Decision  │───▶│   WEEX API  │     │
│  │  Analyst    │    │   Engine    │    │   Executor  │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                  │                  │             │
│         ▼                  ▼                  ▼             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              AI LOG RECORDER                        │   │
│  │  (Competition Compliance)                           │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/akash-mondal/fenyr-trading-agent
cd fenyr-trading-agent

# Install
pip install -r requirements.txt

# Configure
cp config.example.py config.py
# Edit config.py with your API keys

# Run
python main.py
```

## ⚙️ Configuration

Create `config.py` from the template:

```python
# OpenAI
OPENAI_API_KEY = "sk-..."

# WEEX Competition Account
WEEX_API_KEY = "weex_..."
WEEX_SECRET_KEY = "..."
WEEX_PASSPHRASE = "..."

# Trading Parameters
MAX_POSITION_SIZE = 0.001  # BTC
MAX_LEVERAGE = 20
ALLOWED_PAIRS = ["cmt_btcusdt", "cmt_ethusdt", "cmt_solusdt"]
```

## 📊 Supported Strategies

| Strategy | Description |
|----------|-------------|
| RSI Mean Reversion | Buy oversold (<30), sell overbought (>70) |
| Momentum | Follow trend with EMA crossovers |
| Funding Arbitrage | Trade based on funding rate signals |

## 🔄 AI Log Integration

Every trading decision is logged to WEEX for competition compliance:

```python
{
    "stage": "Strategy Generation",
    "model": "gpt-5.2",
    "input": {"market_data": {...}, "prompt": "..."},
    "output": {"signal": "BUY", "confidence": 0.85},
    "explanation": "AI reasoning..."
}
```

## 📦 Dependencies

- `openai>=1.0.0` - GPT-5.2 API
- `requests` - HTTP client
- `pandas` - Data analysis
- `ta` - Technical indicators

## 🔒 Security

- API keys stored in gitignored `config.py`
- Rate limiting built-in
- Max position size limits

## 📜 License

MIT

## 🏆 Hackathon

Built for **AI Wars: WEEX Alpha Awakens** - $880,000 USD prize pool
