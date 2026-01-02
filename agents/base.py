"""
Base Agent Class for Multi-Agent Trading System
All specialized agents inherit from this base class
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
import json

from openai import OpenAI


class Signal(Enum):
    """Trading signal types"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    NEUTRAL = "neutral"
    BULLISH = "bullish"
    BEARISH = "bearish"
    APPROVE = "approve"
    REJECT = "reject"
    REDUCE = "reduce"


class Action(Enum):
    """Final action types"""
    EXECUTE = "execute"
    HOLD = "hold"
    ALERT = "alert"


@dataclass
class AgentDecision:
    """Decision output from an agent"""
    agent_name: str
    stage: str
    signal: Signal
    confidence: float
    reasoning: str
    data: Dict[str, Any]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_ai_log(self) -> Dict[str, Any]:
        """Convert to WEEX AI Log format"""
        return {
            "stage": self.stage,
            "model": "GPT-5.2",
            "input": self.data.get("input", {}),
            "output": {
                "signal": self.signal.value,
                "confidence": self.confidence,
                "agent": self.agent_name,
                **self.data.get("output", {})
            },
            "explanation": self.reasoning[:1000]
        }


class BaseAgent(ABC):
    """Base class for all trading agents"""
    
    def __init__(
        self,
        name: str,
        stage: str,
        openai_client: OpenAI,
        weex_client,
        model: str = "gpt-5.2"
    ):
        self.name = name
        self.stage = stage
        self.openai = openai_client
        self.weex = weex_client
        self.model = model
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the system prompt for this agent"""
        pass
    
    @abstractmethod
    def analyze(self, context: Dict[str, Any]) -> AgentDecision:
        """Perform analysis and return decision"""
        pass
    
    def upload_ai_log(self, decision: AgentDecision, order_id: Optional[int] = None) -> Dict:
        """Upload AI log to WEEX"""
        ai_log = decision.to_ai_log()
        if order_id:
            ai_log["orderId"] = order_id
        
        return self.weex.upload_ai_log(
            stage=ai_log["stage"],
            model=ai_log["model"],
            input_data=ai_log["input"],
            output_data=ai_log["output"],
            explanation=ai_log["explanation"],
            order_id=order_id
        )
    
    def call_gpt(self, prompt: str, context: Dict[str, Any]) -> str:
        """Call GPT with agent's system prompt"""
        response = self.openai.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "user", "content": f"{prompt}\n\nContext:\n{json.dumps(context, indent=2)}"}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
