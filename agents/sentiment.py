"""
Sentiment Agent
Analyzes market sentiment through funding rates and open interest
"""

import json
from typing import Dict, Any

from .base import BaseAgent, AgentDecision, Signal


class SentimentAgent(BaseAgent):
    """Agent specialized in sentiment analysis"""
    
    def __init__(self, openai_client, weex_client, model: str = "gpt-5.2"):
        super().__init__(
            name="SentimentAgent",
            stage="Sentiment Analysis",
            openai_client=openai_client,
            weex_client=weex_client,
            model=model
        )
    
    def get_system_prompt(self) -> str:
        return """You are the Sentiment Agent, specialized in market sentiment analysis.

Your role:
- Analyze funding rates (negative = shorts pay longs, bullish)
- Monitor open interest changes
- Assess market positioning and crowding
- Identify potential squeezes

You receive: funding rate, open interest, volume data
You output: BULLISH, BEARISH, or NEUTRAL signal with confidence 0-1

Format your response as JSON:
{
    "signal": "BULLISH|BEARISH|NEUTRAL",
    "confidence": 0.0-1.0,
    "reasoning": "Your sentiment analysis..."
}"""
    
    def analyze(self, context: Dict[str, Any]) -> AgentDecision:
        """Analyze market sentiment"""
        symbol = context.get("symbol", "cmt_btcusdt")
        
        # Fetch sentiment data
        ticker = self.weex.get_ticker(symbol)
        funding = self.weex.get_funding_rate(symbol)
        
        # Try to get open interest
        try:
            oi = self.weex.get_open_interest(symbol)
            open_interest = oi.get("openInterestAmount", "N/A")
        except:
            open_interest = "N/A"
        
        # Build context
        sentiment_context = {
            "symbol": symbol,
            "funding_rate": funding.get("fundingRate"),
            "next_funding_time": funding.get("fundingTime"),
            "open_interest": open_interest,
            "24h_volume": ticker.get("volume_24h"),
            "24h_change": ticker.get("priceChangePercent"),
            "current_price": ticker.get("last")
        }
        
        # Call GPT for analysis
        prompt = f"Analyze the sentiment for {symbol} based on funding rates and market data."
        response = self.call_gpt(prompt, sentiment_context)
        
        # Parse response
        try:
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
            "BULLISH": Signal.BULLISH,
            "BEARISH": Signal.BEARISH,
            "NEUTRAL": Signal.NEUTRAL
        }
        signal = signal_map.get(result.get("signal", "NEUTRAL").upper(), Signal.NEUTRAL)
        
        return AgentDecision(
            agent_name=self.name,
            stage=self.stage,
            signal=signal,
            confidence=float(result.get("confidence", 0.5)),
            reasoning=result.get("reasoning", ""),
            data={
                "input": sentiment_context,
                "output": {
                    "funding_rate": funding.get("fundingRate"),
                    "sentiment": result.get("signal")
                }
            }
        )
