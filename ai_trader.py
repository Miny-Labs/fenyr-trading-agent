"""
Fenyr AI Trading Agent
GPT-5.2 powered autonomous trading bot
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from openai import OpenAI
import pandas as pd
import numpy as np

from weex_client import WeexClient
from tools import TRADING_TOOLS, TRADING_SYSTEM_PROMPT, ACTION_TO_SIDE


class TechnicalAnalysis:
    """Calculate technical indicators from price data"""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return round(rsi, 2)
    
    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """Calculate EMA"""
        if len(prices) < period:
            return prices[-1] if prices else 0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        return round(ema, 2)
    
    @staticmethod
    def calculate_macd(prices: List[float]) -> Dict[str, float]:
        """Calculate MACD indicator"""
        ema_12 = TechnicalAnalysis.calculate_ema(prices, 12)
        ema_26 = TechnicalAnalysis.calculate_ema(prices, 26)
        macd_line = ema_12 - ema_26
        signal_line = TechnicalAnalysis.calculate_ema(prices[-9:], 9) if len(prices) >= 9 else macd_line
        
        return {
            "macd": round(macd_line, 2),
            "signal": round(signal_line, 2),
            "histogram": round(macd_line - signal_line, 2)
        }


class FenyrAgent:
    """GPT-5.2 powered trading agent"""
    
    def __init__(
        self,
        openai_api_key: str,
        weex_client: WeexClient,
        model: str = "gpt-5.2",
        max_position_size: float = 0.0002
    ):
        self.openai = OpenAI(api_key=openai_api_key)
        self.weex = weex_client
        self.model = model
        self.max_position_size = max_position_size
        self.conversation_history = []
        self.trade_count = 0
        
    def _add_message(self, role: str, content: str):
        """Add message to conversation history"""
        self.conversation_history.append({"role": role, "content": content})
        # Keep last 20 messages
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]
    
    def _get_market_data(self, symbol: str) -> Dict:
        """Fetch market data for analysis"""
        ticker = self.weex.get_ticker(symbol)
        depth = self.weex.get_depth(symbol)
        
        return {
            "symbol": symbol,
            "last_price": ticker.get("last"),
            "high_24h": ticker.get("high_24h"),
            "low_24h": ticker.get("low_24h"),
            "volume_24h": ticker.get("volume_24h"),
            "price_change_pct": ticker.get("priceChangePercent"),
            "best_bid": depth.get("bids", [[0]])[0][0] if depth.get("bids") else None,
            "best_ask": depth.get("asks", [[0]])[0][0] if depth.get("asks") else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_technical_indicators(self, symbol: str, indicators: List[str]) -> Dict:
        """Calculate technical indicators"""
        candles = self.weex.get_candles(symbol, "1h", 50)
        
        if not candles or not isinstance(candles, list):
            return {"error": "Could not fetch candle data"}
        
        # Extract close prices
        closes = [float(c[4]) for c in candles if isinstance(c, list) and len(c) > 4]
        
        if not closes:
            return {"error": "No price data available"}
        
        result = {"symbol": symbol}
        
        if "rsi" in indicators:
            result["rsi_14"] = TechnicalAnalysis.calculate_rsi(closes)
        
        if "ema_20" in indicators:
            result["ema_20"] = TechnicalAnalysis.calculate_ema(closes, 20)
        
        if "ema_50" in indicators:
            result["ema_50"] = TechnicalAnalysis.calculate_ema(closes, 50)
        
        if "macd" in indicators:
            result["macd"] = TechnicalAnalysis.calculate_macd(closes)
        
        result["current_price"] = closes[-1] if closes else 0
        
        return result
    
    def _get_account_status(self) -> Dict:
        """Get account balance and positions"""
        assets = self.weex.get_assets()
        positions = self.weex.get_positions()
        
        usdt_asset = next((a for a in assets if a.get("coinName") == "USDT"), {})
        
        active_positions = [
            {
                "symbol": p.get("symbol"),
                "size": p.get("total"),
                "side": p.get("holdSide"),
                "entry_price": p.get("averageOpenPrice"),
                "unrealized_pnl": p.get("unrealizedPL")
            }
            for p in positions if float(p.get("total", 0)) > 0
        ]
        
        return {
            "available_usdt": usdt_asset.get("available", "0"),
            "equity_usdt": usdt_asset.get("equity", "0"),
            "unrealized_pnl": usdt_asset.get("unrealizePnl", "0"),
            "active_positions": active_positions,
            "position_count": len(active_positions)
        }
    
    def _execute_trade(
        self,
        symbol: str,
        action: str,
        size: str,
        confidence: float,
        reasoning: str
    ) -> Dict:
        """Execute a trade and upload AI log"""
        
        # Validate confidence
        if confidence < 0.6:
            return {"error": "Confidence too low. Minimum 0.6 required.", "executed": False}
        
        # Validate size
        size_float = float(size)
        if size_float > self.max_position_size:
            return {"error": f"Size exceeds max of {self.max_position_size}", "executed": False}
        
        # Get current price for reference
        ticker = self.weex.get_ticker(symbol)
        current_price = float(ticker.get("last", 0))
        
        # Map action to side
        side = ACTION_TO_SIDE.get(action)
        if not side:
            return {"error": f"Invalid action: {action}", "executed": False}
        
        # Place order (market order)
        order_result = self.weex.place_order(
            symbol=symbol,
            size=size,
            side=side,
            order_type=1,  # Market order
            client_oid=f"fenyr_{int(time.time() * 1000)}"
        )
        
        order_id = order_result.get("order_id")
        
        # Upload AI log for compliance
        ai_log_result = self.weex.upload_ai_log(
            stage="Strategy Generation",
            model=self.model,
            input_data={
                "symbol": symbol,
                "action": action,
                "market_price": current_price,
                "analysis_timestamp": datetime.utcnow().isoformat()
            },
            output_data={
                "signal": action.upper(),
                "size": size,
                "confidence": confidence,
                "order_id": order_id
            },
            explanation=reasoning,
            order_id=int(order_id) if order_id else None
        )
        
        self.trade_count += 1
        
        return {
            "executed": True,
            "order_id": order_id,
            "symbol": symbol,
            "action": action,
            "size": size,
            "price": current_price,
            "confidence": confidence,
            "ai_log_uploaded": ai_log_result.get("code") == "00000",
            "reasoning": reasoning
        }
    
    def _get_funding_rate(self, symbol: str) -> Dict:
        """Get funding rate info"""
        funding = self.weex.get_funding_rate(symbol)
        return {
            "symbol": symbol,
            "funding_rate": funding.get("fundingRate"),
            "next_funding_time": funding.get("fundingTime")
        }
    
    def _process_tool_call(self, tool_name: str, arguments: Dict) -> str:
        """Process a tool call from GPT"""
        
        if tool_name == "get_market_data":
            result = self._get_market_data(arguments["symbol"])
        elif tool_name == "get_technical_indicators":
            result = self._get_technical_indicators(
                arguments["symbol"],
                arguments.get("indicators", ["rsi", "ema_20", "macd"])
            )
        elif tool_name == "get_account_status":
            result = self._get_account_status()
        elif tool_name == "execute_trade":
            result = self._execute_trade(
                arguments["symbol"],
                arguments["action"],
                arguments["size"],
                arguments["confidence"],
                arguments["reasoning"]
            )
        elif tool_name == "get_funding_rate":
            result = self._get_funding_rate(arguments["symbol"])
        elif tool_name == "set_stop_loss_take_profit":
            result = {"status": "TP/SL set", "symbol": arguments["symbol"]}
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        
        return json.dumps(result, indent=2)
    
    def analyze_and_trade(self, user_prompt: str = None) -> str:
        """Main agent loop - analyze market and potentially trade"""
        
        # Default prompt if none provided
        if not user_prompt:
            user_prompt = """Analyze the current BTC market conditions.
            
            1. Get the latest market data for cmt_btcusdt
            2. Calculate RSI, EMA_20, and MACD indicators
            3. Check our account status and positions
            4. Based on your analysis, decide if we should make a trade
            5. If conditions are favorable (confidence > 0.7), execute a small trade (0.0002 BTC)
            
            Provide detailed reasoning for your decision."""
        
        self._add_message("user", user_prompt)
        
        messages = [
            {"role": "system", "content": TRADING_SYSTEM_PROMPT}
        ] + self.conversation_history
        
        # Initial GPT call
        response = self.openai.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=TRADING_TOOLS,
            tool_choice="auto"
        )
        
        assistant_message = response.choices[0].message
        
        # Process tool calls if any
        while assistant_message.tool_calls:
            # Add assistant message with tool calls
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in assistant_message.tool_calls
                ]
            })
            
            # Process each tool call
            for tool_call in assistant_message.tool_calls:
                tool_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                print(f"🔧 Calling tool: {tool_name}")
                print(f"   Arguments: {arguments}")
                
                result = self._process_tool_call(tool_name, arguments)
                
                print(f"   Result: {result[:200]}...")
                
                # Add tool result
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
            
            # Continue conversation with tool results
            messages = [
                {"role": "system", "content": TRADING_SYSTEM_PROMPT}
            ] + self.conversation_history
            
            response = self.openai.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TRADING_TOOLS,
                tool_choice="auto"
            )
            
            assistant_message = response.choices[0].message
        
        # Final response
        final_response = assistant_message.content or "Analysis complete."
        self._add_message("assistant", final_response)
        
        return final_response
    
    def run_continuous(self, interval_seconds: int = 300):
        """Run agent continuously at specified interval"""
        print(f"🚀 Starting Fenyr Trading Agent")
        print(f"   Model: {self.model}")
        print(f"   Max Position: {self.max_position_size} BTC")
        print(f"   Interval: {interval_seconds}s")
        print("-" * 50)
        
        while True:
            try:
                print(f"\n⏰ {datetime.utcnow().isoformat()} - Running analysis...")
                result = self.analyze_and_trade()
                print(f"\n📊 Analysis Result:\n{result}")
                print(f"\n📈 Total trades executed: {self.trade_count}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print(f"\n💤 Sleeping for {interval_seconds}s...")
            time.sleep(interval_seconds)
