#!/usr/bin/env python3
"""
Fenyr AI Trading Agent - Main Entry Point
GPT-5.2 powered autonomous trading bot for WEEX AI Wars
"""

import sys
import argparse
from datetime import datetime

import config
from weex_client import create_client
from ai_trader import FenyrAgent


def print_banner():
    """Print startup banner"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ███████╗███████╗███╗   ██╗██╗   ██╗██████╗             ║
║   ██╔════╝██╔════╝████╗  ██║╚██╗ ██╔╝██╔══██╗            ║
║   █████╗  █████╗  ██╔██╗ ██║ ╚████╔╝ ██████╔╝            ║
║   ██╔══╝  ██╔══╝  ██║╚██╗██║  ╚██╔╝  ██╔══██╗            ║
║   ██║     ███████╗██║ ╚████║   ██║   ██║  ██║            ║
║   ╚═╝     ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝            ║
║                                                           ║
║   AI Trading Agent powered by GPT-5.2                     ║
║   Built for WEEX AI Wars Hackathon                        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)


def run_single_analysis(agent: FenyrAgent, symbol: str = "cmt_btcusdt"):
    """Run a single analysis cycle"""
    prompt = f"""Analyze the current {symbol.upper()} market conditions.
    
    1. Get the latest market data for {symbol}
    2. Calculate RSI, EMA_20, EMA_50, and MACD indicators  
    3. Check our account status and existing positions
    4. Based on your technical analysis, evaluate if there's a trading opportunity
    5. If you see a high-confidence opportunity (>0.7), execute a small trade (0.0002 BTC)
    
    Provide detailed analysis and reasoning for your decision.
    Remember: This is for the WEEX AI Wars competition - all trades must be well-reasoned."""
    
    print(f"\n🔍 Analyzing {symbol}...")
    print("-" * 50)
    
    result = agent.analyze_and_trade(prompt)
    
    print(f"\n📊 Analysis Result:")
    print("-" * 50)
    print(result)
    
    return result


def run_demo(agent: FenyrAgent):
    """Run a demo showing agent capabilities"""
    print("\n🎯 Running Demo - Testing Agent Capabilities\n")
    
    # Test 1: Market Data
    print("=" * 60)
    print("TEST 1: Fetching Market Data")
    print("=" * 60)
    result = agent.analyze_and_trade(
        "Get the current market data for cmt_btcusdt and summarize the key metrics."
    )
    print(result)
    
    # Test 2: Technical Analysis
    print("\n" + "=" * 60)
    print("TEST 2: Technical Analysis")
    print("=" * 60)
    result = agent.analyze_and_trade(
        "Calculate RSI, EMA_20, EMA_50, and MACD for cmt_btcusdt. What do these indicators suggest?"
    )
    print(result)
    
    # Test 3: Account Status
    print("\n" + "=" * 60)
    print("TEST 3: Account Status")
    print("=" * 60)
    result = agent.analyze_and_trade(
        "Check our account status. How much USDT do we have available? Any open positions?"
    )
    print(result)
    
    # Test 4: Full Analysis & Trade Decision
    print("\n" + "=" * 60)
    print("TEST 4: Full Analysis & Trade Decision")
    print("=" * 60)
    result = agent.analyze_and_trade(
        """Perform a complete analysis of cmt_btcusdt:
        1. Get current price and orderbook
        2. Calculate all major technical indicators
        3. Check our account and positions
        4. Make a trading decision with full reasoning
        5. If confident (>0.7), execute a small trade (0.0002 BTC)"""
    )
    print(result)
    
    print("\n" + "=" * 60)
    print(f"DEMO COMPLETE - Trades executed: {agent.trade_count}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Fenyr AI Trading Agent")
    parser.add_argument("--mode", choices=["single", "continuous", "demo"], 
                       default="single", help="Operation mode")
    parser.add_argument("--symbol", default="cmt_btcusdt", help="Trading symbol")
    parser.add_argument("--interval", type=int, default=300, 
                       help="Interval in seconds for continuous mode")
    
    args = parser.parse_args()
    
    print_banner()
    
    print(f"📅 Started: {datetime.utcnow().isoformat()}")
    print(f"🤖 Model: {config.GPT_MODEL}")
    print(f"📊 Symbol: {args.symbol}")
    print(f"🔄 Mode: {args.mode}")
    
    # Initialize WEEX client
    print("\n🔗 Connecting to WEEX Exchange...")
    weex_client = create_client(
        api_key=config.WEEX_API_KEY,
        secret_key=config.WEEX_SECRET_KEY,
        passphrase=config.WEEX_PASSPHRASE,
        base_url=config.WEEX_BASE_URL
    )
    
    # Test connection
    try:
        ticker = weex_client.get_ticker(args.symbol)
        print(f"✅ Connected! {args.symbol} = ${ticker.get('last')}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        sys.exit(1)
    
    # Initialize AI agent
    print("\n🧠 Initializing AI Agent...")
    agent = FenyrAgent(
        openai_api_key=config.OPENAI_API_KEY,
        weex_client=weex_client,
        model=config.GPT_MODEL,
        max_position_size=config.MAX_POSITION_SIZE_BTC
    )
    print("✅ Agent ready!")
    
    # Run based on mode
    if args.mode == "demo":
        run_demo(agent)
    elif args.mode == "continuous":
        agent.run_continuous(args.interval)
    else:
        run_single_analysis(agent, args.symbol)
    
    print(f"\n📈 Total trades executed: {agent.trade_count}")
    print("🏁 Fenyr Agent finished.")


if __name__ == "__main__":
    main()
