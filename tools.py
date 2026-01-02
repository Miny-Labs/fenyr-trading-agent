"""
Trading Tools for GPT-5.2 Function Calling
Defines the tools/functions that GPT can call to interact with the market
"""

# Tool definitions for OpenAI function calling
TRADING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_market_data",
            "description": "Get current market data including price, orderbook, and recent trades for analysis. Use this to understand current market conditions before making trading decisions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading pair symbol (e.g., cmt_btcusdt, cmt_ethusdt)",
                        "enum": ["cmt_btcusdt", "cmt_ethusdt", "cmt_solusdt", "cmt_dogeusdt"]
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_technical_indicators",
            "description": "Calculate technical indicators (RSI, EMA, MACD) from recent price data. Use this to identify trading signals based on technical analysis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading pair symbol"
                    },
                    "indicators": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of indicators to calculate: rsi, ema_20, ema_50, macd, bollinger"
                    }
                },
                "required": ["symbol", "indicators"]
            }
        }
    },
    {
        "type": "function", 
        "function": {
            "name": "get_account_status",
            "description": "Get current account status including balance, equity, and open positions. Use this to understand available capital and risk exposure.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_trade",
            "description": "Execute a trade order. Only call this when you have high confidence in your analysis and clear reasoning. IMPORTANT: Always provide detailed reasoning.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading pair to trade"
                    },
                    "action": {
                        "type": "string",
                        "enum": ["open_long", "close_long", "open_short", "close_short"],
                        "description": "Trade action to execute"
                    },
                    "size": {
                        "type": "string",
                        "description": "Position size in base currency (e.g., '0.0002' for BTC)"
                    },
                    "confidence": {
                        "type": "number",
                        "description": "Confidence level 0-1 for this trade"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Detailed reasoning for this trade decision. This will be logged for compliance."
                    }
                },
                "required": ["symbol", "action", "size", "confidence", "reasoning"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_funding_rate",
            "description": "Get current and predicted funding rate for futures. Useful for funding rate arbitrage strategies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading pair symbol"
                    }
                },
                "required": ["symbol"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_stop_loss_take_profit",
            "description": "Set stop loss and take profit levels for risk management.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Trading pair"
                    },
                    "stop_loss_price": {
                        "type": "string",
                        "description": "Stop loss price"
                    },
                    "take_profit_price": {
                        "type": "string",
                        "description": "Take profit price"
                    }
                },
                "required": ["symbol"]
            }
        }
    }
]


# System prompt for the trading agent
TRADING_SYSTEM_PROMPT = """You are Fenyr, an AI trading agent specialized in cryptocurrency futures trading on WEEX Exchange.

Your objective is to analyze market data and make profitable trading decisions while managing risk.

## Your Capabilities:
1. Fetch real-time market data (prices, orderbook, volume)
2. Calculate technical indicators (RSI, EMA, MACD, Bollinger Bands)
3. Check account status and positions
4. Execute trades with confidence scoring
5. Monitor funding rates for arbitrage opportunities

## Trading Rules:
- Maximum leverage: 20x (competition limit)
- Allowed pairs: cmt_btcusdt, cmt_ethusdt, cmt_solusdt, cmt_dogeusdt, cmt_xrpusdt, cmt_adausdt, cmt_bnbusdt, cmt_ltcusdt
- Always provide detailed reasoning for every trade
- Minimum confidence of 0.6 to execute a trade
- Maximum position size: 0.001 BTC equivalent

## Risk Management:
- Never risk more than 2% of account per trade
- Always consider current positions before opening new ones
- Use stop losses when appropriate

## Analysis Process:
1. First, get current market data
2. Calculate relevant technical indicators
3. Check account status and existing positions
4. Analyze the data and form a thesis
5. If conditions are favorable, execute a trade with full reasoning

Be analytical, data-driven, and always explain your thought process.
"""


# Action to side mapping for WEEX API
ACTION_TO_SIDE = {
    "open_long": 1,
    "close_short": 2,
    "open_short": 3,
    "close_long": 4
}
