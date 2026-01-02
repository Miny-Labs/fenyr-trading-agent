"""
Coordinator Agent
Orchestrates the team and makes final decisions
"""

import json
from typing import Dict, Any, List
from dataclasses import dataclass

from .base import BaseAgent, AgentDecision, Signal, Action
from .market_analyst import MarketAnalystAgent
from .sentiment import SentimentAgent
from .risk_manager import RiskManagerAgent
from .executor import ExecutorAgent


@dataclass
class TeamDecision:
    """Final decision from agent team"""
    action: Action
    trade_direction: str  # "buy", "sell", or "none"
    size: str
    confidence: float
    reasoning: str
    agent_decisions: List[AgentDecision]


class CoordinatorAgent(BaseAgent):
    """Orchestrates the multi-agent team"""
    
    def __init__(self, openai_client, weex_client, model: str = "gpt-5.2",
                 max_position_size: float = 0.0002):
        super().__init__(
            name="Coordinator",
            stage="Decision Making",
            openai_client=openai_client,
            weex_client=weex_client,
            model=model
        )
        self.max_position_size = max_position_size
        
        # Initialize team
        self.market_analyst = MarketAnalystAgent(openai_client, weex_client, model)
        self.sentiment_agent = SentimentAgent(openai_client, weex_client, model)
        self.risk_manager = RiskManagerAgent(openai_client, weex_client, model, max_position_size)
        self.executor = ExecutorAgent(openai_client, weex_client, model)
    
    def get_system_prompt(self) -> str:
        return """You are the Coordinator Agent, the leader of the trading team.

Your role:
- Collect analysis from all team members
- Run consensus voting algorithm
- Make final EXECUTE, HOLD, or ALERT decision
- Ensure all decisions are well-reasoned

Voting weights:
- Market Analyst: 35%
- Sentiment Agent: 25%
- Risk Manager: 40% (has veto power)

Thresholds:
- EXECUTE: weighted confidence >= 0.65
- ALERT: weighted confidence 0.45-0.65
- HOLD: weighted confidence < 0.45

If Risk Manager says REJECT, always HOLD regardless of other signals."""
    
    def calculate_consensus(self, decisions: Dict[str, AgentDecision]) -> Dict[str, Any]:
        """Calculate weighted consensus from agent decisions"""
        
        weights = {
            "MarketAnalyst": 0.35,
            "SentimentAgent": 0.25,
            "RiskManager": 0.40
        }
        
        # Check for risk veto
        risk_decision = decisions.get("RiskManager")
        if risk_decision and risk_decision.signal == Signal.REJECT:
            return {
                "action": Action.HOLD,
                "confidence": 0.0,
                "reason": "Risk Manager veto - trade rejected"
            }
        
        # Calculate weighted score
        total_score = 0
        direction_votes = {"buy": 0, "sell": 0, "hold": 0}
        
        for agent_name, decision in decisions.items():
            if agent_name not in weights:
                continue
            
            weight = weights[agent_name]
            score = decision.confidence * weight
            
            # Determine direction
            if decision.signal in [Signal.BUY, Signal.BULLISH, Signal.APPROVE]:
                total_score += score
                direction_votes["buy"] += weight
            elif decision.signal in [Signal.SELL, Signal.BEARISH]:
                total_score += score
                direction_votes["sell"] += weight
            else:
                direction_votes["hold"] += weight
        
        # Determine action and direction
        if total_score >= 0.65:
            action = Action.EXECUTE
        elif total_score >= 0.45:
            action = Action.ALERT
        else:
            action = Action.HOLD
        
        # Determine trade direction
        if direction_votes["buy"] > direction_votes["sell"]:
            direction = "buy"
        elif direction_votes["sell"] > direction_votes["buy"]:
            direction = "sell"
        else:
            direction = "none"
        
        return {
            "action": action,
            "confidence": total_score,
            "direction": direction,
            "votes": direction_votes
        }
    
    def run_team_analysis(self, symbol: str) -> TeamDecision:
        """Run full team analysis and return decision"""
        
        print(f"\n{'='*60}")
        print(f"🤖 MULTI-AGENT TEAM ANALYSIS: {symbol}")
        print(f"{'='*60}\n")
        
        decisions = {}
        
        # 1. Market Analyst
        print("📊 [1/4] Market Analyst analyzing...")
        ma_decision = self.market_analyst.analyze({"symbol": symbol})
        decisions["MarketAnalyst"] = ma_decision
        print(f"   Signal: {ma_decision.signal.value} | Confidence: {ma_decision.confidence}")
        
        # Upload AI Log
        ma_log = self.market_analyst.upload_ai_log(ma_decision)
        print(f"   AI Log: {'✅' if ma_log.get('code') == '00000' else '❌'}")
        
        # 2. Sentiment Agent
        print("\n💭 [2/4] Sentiment Agent analyzing...")
        sa_decision = self.sentiment_agent.analyze({"symbol": symbol})
        decisions["SentimentAgent"] = sa_decision
        print(f"   Signal: {sa_decision.signal.value} | Confidence: {sa_decision.confidence}")
        
        # Upload AI Log
        sa_log = self.sentiment_agent.upload_ai_log(sa_decision)
        print(f"   AI Log: {'✅' if sa_log.get('code') == '00000' else '❌'}")
        
        # 3. Risk Manager
        print("\n🛡️ [3/4] Risk Manager assessing...")
        rm_context = {
            "symbol": symbol,
            "proposed_signal": ma_decision.signal.value,
            "proposed_confidence": ma_decision.confidence
        }
        rm_decision = self.risk_manager.analyze(rm_context)
        decisions["RiskManager"] = rm_decision
        print(f"   Signal: {rm_decision.signal.value} | Confidence: {rm_decision.confidence}")
        
        # Upload AI Log
        rm_log = self.risk_manager.upload_ai_log(rm_decision)
        print(f"   AI Log: {'✅' if rm_log.get('code') == '00000' else '❌'}")
        
        # 4. Coordinator consensus
        print("\n🎯 [4/4] Coordinator calculating consensus...")
        consensus = self.calculate_consensus(decisions)
        
        # Get recommended size from risk manager
        recommended_size = str(rm_decision.data.get("output", {}).get("recommended_size", self.max_position_size))
        
        # Build coordinator decision
        coord_reasoning = f"Consensus: {consensus['action'].value}. Weighted confidence: {consensus['confidence']:.2f}. Direction: {consensus['direction']}. Votes: {consensus['votes']}"
        
        coord_decision = AgentDecision(
            agent_name=self.name,
            stage=self.stage,
            signal=Signal.BUY if consensus["direction"] == "buy" else Signal.SELL if consensus["direction"] == "sell" else Signal.HOLD,
            confidence=consensus["confidence"],
            reasoning=coord_reasoning,
            data={
                "input": {"agent_decisions": [d.signal.value for d in decisions.values()]},
                "output": {
                    "action": consensus["action"].value,
                    "confidence": consensus["confidence"],
                    "direction": consensus["direction"],
                    "votes": consensus["votes"]
                }
            }
        )
        
        # Upload Coordinator AI Log
        coord_log = self.upload_ai_log(coord_decision)
        print(f"   Decision: {consensus['action'].value} | Confidence: {consensus['confidence']:.2f}")
        print(f"   AI Log: {'✅' if coord_log.get('code') == '00000' else '❌'}")
        
        # 5. Execute if needed
        execution_decision = None
        if consensus["action"] == Action.EXECUTE and consensus["direction"] in ["buy", "sell"]:
            print(f"\n⚡ [5/5] Executor placing order...")
            
            exec_context = {
                "action": "execute",
                "symbol": symbol,
                "size": recommended_size,
                "trade_direction": consensus["direction"],
                "reasoning": coord_reasoning
            }
            
            execution_decision = self.executor.analyze(exec_context)
            
            # Get order ID and upload AI Log
            order_id = execution_decision.data.get("output", {}).get("order_id")
            exec_log = self.executor.upload_ai_log(execution_decision, order_id=int(order_id) if order_id else None)
            print(f"   Order ID: {order_id}")
            print(f"   AI Log: {'✅' if exec_log.get('code') == '00000' else '❌'}")
        else:
            print(f"\n⏸️ [5/5] No execution - {consensus['action'].value}")
        
        print(f"\n{'='*60}")
        print(f"✅ TEAM ANALYSIS COMPLETE")
        print(f"{'='*60}\n")
        
        return TeamDecision(
            action=consensus["action"],
            trade_direction=consensus["direction"],
            size=recommended_size,
            confidence=consensus["confidence"],
            reasoning=coord_reasoning,
            agent_decisions=list(decisions.values()) + ([execution_decision] if execution_decision else [])
        )
    
    def analyze(self, context: Dict[str, Any]) -> AgentDecision:
        """Coordinator analysis (wraps team analysis)"""
        symbol = context.get("symbol", "cmt_btcusdt")
        team_decision = self.run_team_analysis(symbol)
        
        return AgentDecision(
            agent_name=self.name,
            stage=self.stage,
            signal=Signal.BUY if team_decision.trade_direction == "buy" else Signal.SELL if team_decision.trade_direction == "sell" else Signal.HOLD,
            confidence=team_decision.confidence,
            reasoning=team_decision.reasoning,
            data={
                "input": context,
                "output": {
                    "action": team_decision.action.value,
                    "direction": team_decision.trade_direction,
                    "size": team_decision.size
                }
            }
        )
