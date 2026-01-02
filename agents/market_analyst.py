"""
Market Analyst Agent
Performs technical analysis on price data
"""

import json
from typing import Dict, Any, List
import numpy as np

from .base import BaseAgent, AgentDecision, Signal


class MarketAnalystAgent(BaseAgent):
    """Agent specialized in technical analysis"""
    
    def __init__(self, openai_client, weex_client, model: str = "gpt-5.2"):
        super().__init__(
            name="MarketAnalyst",
            stage="Technical Analysis",
            openai_client=openai_client,
            weex_client=weex_client,
            model=model
        )
    
    def get_system_prompt(self) -> str:
        return """You are the Market Analyst Agent, specialized in technical analysis.

Your role:
- Analyze price action and technical indicators
- Identify trends, support/resistance levels
- Generate trading signals based on technical patterns

You receive: RSI, EMA, MACD, price data, orderbook
You output: BUY, SELL, or NEUTRAL signal with confidence 0-1

Be precise and data-driven. Format your response as JSON:
{
    "signal": "BUY|SELL|NEUTRAL",
    "confidence": 0.0-1.0,
    "reasoning": "Your technical analysis..."
}"""
    
    def calculate_indicators(self, candles: List) -> Dict[str, Any]:
        """Calculate technical indicators from candle data"""
        if not candles or len(candles) < 20:
            return {}
        
        closes = [float(c[4]) for c in candles if isinstance(c, list) and len(c) > 4]
        
        # RSI
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else 0
        avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else 1
        rs = avg_gain / avg_loss if avg_loss > 0 else 100
        rsi = 100 - (100 / (1 + rs))
        
        # EMAs
        def ema(data, period):
            multiplier = 2 / (period + 1)
            result = data[0]
            for price in data[1:]:
                result = (price - result) * multiplier + result
            return result
        
        ema_20 = ema(closes, 20)
        ema_50 = ema(closes, 50) if len(closes) >= 50 else ema_20
        
        # MACD
        ema_12 = ema(closes, 12)
        ema_26 = ema(closes, 26) if len(closes) >= 26 else ema_12
        macd = ema_12 - ema_26
        
        return {
            "rsi_14": round(rsi, 2),
            "ema_20": round(ema_20, 2),
            "ema_50": round(ema_50, 2),
            "macd": round(macd, 2),
            "current_price": closes[-1],
            "price_above_ema20": closes[-1] > ema_20,
            "price_above_ema50": closes[-1] > ema_50,
            "ema_bullish_cross": ema_20 > ema_50
        }
    
    def analyze(self, context: Dict[str, Any]) -> AgentDecision:
        """Analyze market using technical indicators"""
        symbol = context.get("symbol", "cmt_btcusdt")
        
        # Fetch data
        ticker = self.weex.get_ticker(symbol)
        candles = self.weex.get_candles(symbol, "1h", 50)
        depth = self.weex.get_depth(symbol)
        
        # Calculate indicators
        indicators = self.calculate_indicators(candles)
        
        # Build context for GPT
        analysis_context = {
            "symbol": symbol,
            "current_price": ticker.get("last"),
            "24h_high": ticker.get("high_24h"),
            "24h_low": ticker.get("low_24h"),
            "24h_change": ticker.get("priceChangePercent"),
            "indicators": indicators,
            "orderbook": {
                "best_bid": depth.get("bids", [[0]])[0][0] if depth.get("bids") else None,
                "best_ask": depth.get("asks", [[0]])[0][0] if depth.get("asks") else None
            }
        }
        
        # Call GPT for analysis
        prompt = f"Analyze {symbol} and provide a trading signal based on the technical data."
        response = self.call_gpt(prompt, analysis_context)
        
        # Parse response
        try:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(response[start:end])
            else:
                result = {"signal": "NEUTRAL", "confidence": 0.5, "reasoning": response}
        except:
            result = {"signal": "NEUTRAL", "confidence": 0.5, "reasoning": response}
        
        # Map signal
        signal_map = {
            "BUY": Signal.BUY,
            "SELL": Signal.SELL,
            "NEUTRAL": Signal.NEUTRAL,
            "HOLD": Signal.HOLD
        }
        signal = signal_map.get(result.get("signal", "NEUTRAL").upper(), Signal.NEUTRAL)
        
        return AgentDecision(
            agent_name=self.name,
            stage=self.stage,
            signal=signal,
            confidence=float(result.get("confidence", 0.5)),
            reasoning=result.get("reasoning", ""),
            data={
                "input": analysis_context,
                "output": {"indicators": indicators}
            }
        )
