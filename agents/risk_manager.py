"""
Risk Manager Agent
Assesses risk and determines position sizing
"""

import json
from typing import Dict, Any

from .base import BaseAgent, AgentDecision, Signal


class RiskManagerAgent(BaseAgent):
    """Agent specialized in risk management"""
    
    def __init__(self, openai_client, weex_client, model: str = "gpt-5.2", 
                 max_position_size: float = 0.0002,
                 max_risk_pct: float = 0.02):
        super().__init__(
            name="RiskManager",
            stage="Risk Assessment",
            openai_client=openai_client,
            weex_client=weex_client,
            model=model
        )
        self.max_position_size = max_position_size
        self.max_risk_pct = max_risk_pct
    
    def get_system_prompt(self) -> str:
        return f"""You are the Risk Manager Agent, the guardian of capital.

Your role:
- Assess current portfolio exposure
- Calculate appropriate position sizing
- Enforce risk limits (max {self.max_risk_pct*100}% per trade)
- Veto trades that exceed risk tolerance

You receive: account balance, positions, proposed trade
You output: APPROVE, REDUCE, or REJECT with recommended size

You have VETO POWER - if risk is too high, REJECT the trade.

Max position size: {self.max_position_size} BTC

Format your response as JSON:
{{
    "signal": "APPROVE|REDUCE|REJECT",
    "confidence": 0.0-1.0,
    "recommended_size": 0.0001-{self.max_position_size},
    "reasoning": "Your risk assessment..."
}}"""
    
    def analyze(self, context: Dict[str, Any]) -> AgentDecision:
        """Assess risk for proposed trade"""
        symbol = context.get("symbol", "cmt_btcusdt")
        proposed_signal = context.get("proposed_signal", "BUY")
        proposed_confidence = context.get("proposed_confidence", 0.5)
        
        # Fetch account data
        assets = self.weex.get_assets()
        positions = self.weex.get_positions()
        
        # Parse account info
        usdt_asset = next((a for a in assets if a.get("coinName") == "USDT"), {})
        available = float(usdt_asset.get("available", 0))
        equity = float(usdt_asset.get("equity", 0))
        
        # Check current exposure
        active_positions = [
            {
                "symbol": p.get("symbol"),
                "size": p.get("total"),
                "side": p.get("holdSide"),
                "pnl": p.get("unrealizedPL")
            }
            for p in positions if float(p.get("total", 0)) > 0
        ]
        
        # Get current price
        ticker = self.weex.get_ticker(symbol)
        current_price = float(ticker.get("last", 0))
        
        # Build context
        risk_context = {
            "symbol": symbol,
            "proposed_signal": proposed_signal,
            "proposed_confidence": proposed_confidence,
            "account": {
                "available_usdt": available,
                "equity_usdt": equity,
                "active_positions": active_positions,
                "position_count": len(active_positions)
            },
            "risk_limits": {
                "max_risk_pct": self.max_risk_pct,
                "max_position_size": self.max_position_size
            },
            "current_price": current_price
        }
        
        # Call GPT for assessment
        prompt = f"Assess the risk for a potential {proposed_signal} trade on {symbol}. Should we proceed?"
        response = self.call_gpt(prompt, risk_context)
        
        # Parse response
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(response[start:end])
            else:
                result = {"signal": "APPROVE", "confidence": 0.7, "recommended_size": self.max_position_size, "reasoning": response}
        except:
            result = {"signal": "APPROVE", "confidence": 0.7, "recommended_size": self.max_position_size, "reasoning": response}
        
        # Map signal
        signal_map = {
            "APPROVE": Signal.APPROVE,
            "REDUCE": Signal.REDUCE,
            "REJECT": Signal.REJECT
        }
        signal = signal_map.get(result.get("signal", "APPROVE").upper(), Signal.APPROVE)
        
        # Ensure recommended size is within limits
        recommended_size = min(
            float(result.get("recommended_size", self.max_position_size)),
            self.max_position_size
        )
        
        return AgentDecision(
            agent_name=self.name,
            stage=self.stage,
            signal=signal,
            confidence=float(result.get("confidence", 0.7)),
            reasoning=result.get("reasoning", ""),
            data={
                "input": risk_context,
                "output": {
                    "recommended_size": recommended_size,
                    "risk_status": result.get("signal")
                }
            }
        )
