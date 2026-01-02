# Fenyr Trading Agent Configuration Template
# Copy this to config.py and fill in your keys

# OpenAI API
OPENAI_API_KEY = "sk-proj-YOUR_KEY_HERE"

# WEEX Competition Account
WEEX_API_KEY = "weex_YOUR_KEY_HERE"
WEEX_SECRET_KEY = "YOUR_SECRET_HERE"
WEEX_PASSPHRASE = "YOUR_PASSPHRASE_HERE"
WEEX_BASE_URL = "https://api-contract.weex.com"

# Trading Parameters
MAX_POSITION_SIZE_BTC = 0.001  # Maximum position size in BTC
MAX_LEVERAGE = 20              # Competition limit
MIN_TRADE_VALUE_USDT = 12      # Minimum trade value

# Allowed trading pairs (competition requirement)
ALLOWED_PAIRS = [
    "cmt_btcusdt",
    "cmt_ethusdt", 
    "cmt_solusdt",
    "cmt_dogeusdt",
    "cmt_xrpusdt",
    "cmt_adausdt",
    "cmt_bnbusdt",
    "cmt_ltcusdt"
]

# GPT Model
GPT_MODEL = "gpt-5.2"

# Trading strategy
DEFAULT_STRATEGY = "momentum"  # Options: "rsi", "momentum", "funding"

# Risk management
STOP_LOSS_PCT = 0.02  # 2% stop loss
TAKE_PROFIT_PCT = 0.04  # 4% take profit
