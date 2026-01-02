"""
Executor Agent
Handles order execution and management
"""

import time
from typing import Dict, Any, Optional

from .base import BaseAgent, AgentDecision, Signal


class ExecutorAgent(BaseAgent):
    """Agent specialized in order execution"""
    
    def __init__(self, openai_client, weex_client, model: str = "gpt-5.2"):
        super().__init__(
            name="Executor",
            stage="Order Execution",
            openai_client=openai_client,
            weex_client=weex_client,
            model=model
        )
    
    def get_system_prompt(self) -> str:
        return """You are the Executor Agent, responsible for order execution.

Your role:
- Execute trades based on team consensus
- Manage order placement
- Track fill status
- Set stop-loss and take-profit levels

You execute the final decision from the Coordinator.
Report execution status clearly."""
    
    def execute_trade(
        self,
        symbol: str,
        action: str,  # "buy" or "sell"
        size: str,
        reasoning: str
    ) -> Dict[str, Any]:
        """Execute a market order"""
        
        # Map action to WEEX side
        # 1=open_long, 2=close_short, 3=open_short, 4=close_long
        side_map = {
            "buy": 1,   # open_long
            "sell": 3,  # open_short
        }
        side = side_map.get(action.lower(), 1)
        
        # Get current price
        ticker = self.weex.get_ticker(symbol)
        current_price = float(ticker.get("last", 0))
        
        # Place market order
        order_result = self.weex.place_order(
            symbol=symbol,
            size=size,
            side=side,
            order_type=1,  # Market order
            client_oid=f"fenyr_multi_{int(time.time() * 1000)}"
        )
        
        order_id = order_result.get("order_id")
        
        return {
            "success": order_id is not None,
            "order_id": order_id,
            "symbol": symbol,
            "action": action,
            "size": size,
            "fill_price": current_price,
            "reasoning": reasoning
        }
    
    def analyze(self, context: Dict[str, Any]) -> AgentDecision:
        """Execute based on coordinator decision"""
        action = context.get("action", "hold")
        symbol = context.get("symbol", "cmt_btcusdt")
        size = context.get("size", "0.0002")
        reasoning = context.get("reasoning", "")
        
        if action.lower() in ["execute", "buy", "sell"]:
            # Determine buy or sell
            trade_action = context.get("trade_direction", "buy")
            
            # Execute the trade
            result = self.execute_trade(symbol, trade_action, size, reasoning)
            
            signal = Signal.BUY if trade_action == "buy" else Signal.SELL
            
            return AgentDecision(
                agent_name=self.name,
                stage=self.stage,
                signal=signal,
                confidence=1.0 if result["success"] else 0.0,
                reasoning=f"Executed {trade_action} order: {result}",
                data={
                    "input": context,
                    "output": result
                }
            )
        else:
            return AgentDecision(
                agent_name=self.name,
                stage=self.stage,
                signal=Signal.HOLD,
                confidence=1.0,
                reasoning=f"No execution required. Action: {action}",
                data={
                    "input": context,
                    "output": {"action": "hold", "reason": "No trade signal"}
                }
            )
