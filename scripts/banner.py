#!/usr/bin/env python3
import json

LOGO = r'''
██████╗  ██████╗ ███╗   ██╗███████╗██╗ ██████╗██╗      █████╗ ██╗    ██╗
██╔══██╗██╔═══██╗████╗  ██║╚══███╔╝██║██╔════╝██║     ██╔══██╗██║    ██║
██████╔╝██║   ██║██╔██╗ ██║  ███╔╝ ██║██║     ██║     ███████║██║ █╗ ██║
██╔═══╝ ██║   ██║██║╚██╗██║ ███╔╝  ██║██║     ██║     ██╔══██║██║███╗██║
██║     ╚██████╔╝██║ ╚████║███████╗██║╚██████╗███████╗██║  ██║╚███╔███╔╝
╚═╝      ╚═════╝ ╚═╝  ╚═══╝╚══════╝╚═╝ ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝
'''

CAPABILITIES = [
    "Live market + game data snapshots (price, Torii SQL)",
    "Analytics Q&A (most-used token, drops, land health, closed PnL)",
    "ASCII 3x3 land map with center tile + neighbor tax/price context",
    "Strategy proposals (conservative/balanced/aggressive)",
    "Land buy plan generation with fallback across candidate lands",
    "AVNU swap quote/build/execute flows",
    "Guarded transaction execution (confirm gate + duplicate cooldown)",
    "Structured PnL reporting by token + per-position rows",
    "Daily/on-demand reporting",
]

if __name__ == "__main__":
    print(LOGO)
    print("PonziClaw capabilities:")
    for i, c in enumerate(CAPABILITIES, 1):
        print(f"{i}. {c}")
    print("\nJSON:")
    print(json.dumps({"capabilities": CAPABILITIES}, indent=2))
