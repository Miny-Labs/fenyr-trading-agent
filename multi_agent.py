#!/usr/bin/env python3
"""
Fenyr Multi-Agent Trading System
Team of AI agents collaborating with real conversations
"""

import sys
import argparse
import time
from datetime import datetime
from openai import OpenAI

import config
from weex_client import create_client
from agents import CoordinatorAgent, Signal, Action


def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗███████╗███╗   ██╗██╗   ██╗██████╗                 ║
║   ██╔════╝██╔════╝████╗  ██║╚██╗ ██╔╝██╔══██╗                ║
║   █████╗  █████╗  ██╔██╗ ██║ ╚████╔╝ ██████╔╝                ║
║   ██╔══╝  ██╔══╝  ██║╚██╗██║  ╚██╔╝  ██╔══██╗                ║
║   ██║     ███████╗██║ ╚████║   ██║   ██║  ██║                ║
║   ╚═╝     ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝                ║
║                                                               ║
║   MULTI-AGENT TRADING SYSTEM                                  ║
║   5 AI Agents • Team Consensus • HFT Ready                    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)


def run_single_team_analysis(coordinator: CoordinatorAgent, symbol: str):
    """Run single team analysis cycle"""
    print(f"\n⏰ {datetime.utcnow().isoformat()} - Starting team analysis")
    
    team_decision = coordinator.run_team_analysis(symbol)
    
    print(f"\n📋 TEAM DECISION SUMMARY:")
    print(f"   Action: {team_decision.action.value.upper()}")
    print(f"   Direction: {team_decision.trade_direction}")
    print(f"   Size: {team_decision.size}")
    print(f"   Confidence: {team_decision.confidence:.2f}")
    print(f"   AI Logs Uploaded: {len(team_decision.agent_decisions)}")
    
    return team_decision


def run_hft_mode(coordinator: CoordinatorAgent, symbol: str, cycles: int = 10, interval: float = 30):
    """
    High-Frequency Trading Mode
    Runs rapid analysis cycles with quick decisions
    """
    print(f"\n🚀 HFT MODE ACTIVATED")
    print(f"   Symbol: {symbol}")
    print(f"   Cycles: {cycles}")
    print(f"   Interval: {interval}s")
    print("-" * 60)
    
    trades_executed = 0
    total_ai_logs = 0
    
    for cycle in range(1, cycles + 1):
        print(f"\n{'='*60}")
        print(f"🔄 HFT CYCLE {cycle}/{cycles}")
        print(f"{'='*60}")
        
        try:
            team_decision = coordinator.run_team_analysis(symbol)
            
            total_ai_logs += len(team_decision.agent_decisions)
            
            if team_decision.action == Action.EXECUTE:
                trades_executed += 1
                print(f"⚡ TRADE EXECUTED: {team_decision.trade_direction} {team_decision.size}")
            elif team_decision.action == Action.ALERT:
                print(f"🔔 ALERT: Market conditions notable but not actionable")
            else:
                print(f"⏸️ HOLD: Waiting for better opportunity")
            
        except Exception as e:
            print(f"❌ Cycle error: {e}")
        
        if cycle < cycles:
            print(f"\n💤 Next cycle in {interval}s...")
            time.sleep(interval)
    
    print(f"\n{'='*60}")
    print(f"🏁 HFT SESSION COMPLETE")
    print(f"{'='*60}")
    print(f"   Cycles: {cycles}")
    print(f"   Trades Executed: {trades_executed}")
    print(f"   AI Logs Uploaded: {total_ai_logs}")


def run_continuous_team(coordinator: CoordinatorAgent, symbol: str, interval: int = 300):
    """Run continuous team analysis"""
    print(f"\n🔄 CONTINUOUS TEAM MODE")
    print(f"   Interval: {interval}s")
    
    cycle = 0
    while True:
        cycle += 1
        print(f"\n{'='*60}")
        print(f"CYCLE {cycle}")
        print(f"{'='*60}")
        
        try:
            run_single_team_analysis(coordinator, symbol)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print(f"\n💤 Next analysis in {interval}s...")
        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description="Fenyr Multi-Agent Trading System")
    parser.add_argument("--mode", choices=["single", "continuous", "hft"],
                       default="single", help="Operation mode")
    parser.add_argument("--symbol", default="cmt_btcusdt", help="Trading symbol")
    parser.add_argument("--interval", type=int, default=300,
                       help="Interval in seconds for continuous mode")
    parser.add_argument("--hft-cycles", type=int, default=5,
                       help="Number of HFT cycles")
    parser.add_argument("--hft-interval", type=float, default=30,
                       help="Interval between HFT cycles in seconds")
    
    args = parser.parse_args()
    
    print_banner()
    
    print(f"📅 Started: {datetime.utcnow().isoformat()}")
    print(f"🤖 Model: {config.GPT_MODEL}")
    print(f"📊 Symbol: {args.symbol}")
    print(f"🔄 Mode: {args.mode}")
    
    # Initialize clients
    print("\n🔗 Connecting to WEEX Exchange...")
    weex_client = create_client(
        api_key=config.WEEX_API_KEY,
        secret_key=config.WEEX_SECRET_KEY,
        passphrase=config.WEEX_PASSPHRASE,
        base_url=config.WEEX_BASE_URL
    )
    
    ticker = weex_client.get_ticker(args.symbol)
    print(f"✅ Connected! {args.symbol} = ${ticker.get('last')}")
    
    # Initialize OpenAI
    print("\n🧠 Initializing AI Agents...")
    openai_client = OpenAI(api_key=config.OPENAI_API_KEY)
    
    # Initialize Coordinator (sets up all agents)
    coordinator = CoordinatorAgent(
        openai_client=openai_client,
        weex_client=weex_client,
        model=config.GPT_MODEL,
        max_position_size=config.MAX_POSITION_SIZE_BTC
    )
    
    print("✅ All 5 agents initialized!")
    print("   📊 Market Analyst")
    print("   💭 Sentiment Agent")
    print("   🛡️ Risk Manager")
    print("   ⚡ Executor")
    print("   🎯 Coordinator")
    
    # Run based on mode
    if args.mode == "hft":
        run_hft_mode(coordinator, args.symbol, args.hft_cycles, args.hft_interval)
    elif args.mode == "continuous":
        run_continuous_team(coordinator, args.symbol, args.interval)
    else:
        run_single_team_analysis(coordinator, args.symbol)
    
    print("\n🏁 Fenyr Multi-Agent System finished.")


if __name__ == "__main__":
    main()
