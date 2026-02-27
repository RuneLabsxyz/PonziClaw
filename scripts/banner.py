#!/usr/bin/env python3
import argparse
import json
import urllib.request

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
    "Referral tools (fetch your referral code/link)",
]


def fetch_referral(address: str) -> dict:
    addr = address.lower()
    if addr.startswith("0x") and len(addr) == 66 and not addr.startswith("0x0"):
        addr = "0x0" + addr[2:]
    url = f"https://ponzi.land/api/{addr}/referral-code"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    code = payload.get("referralCode")
    if not code:
        return {"ok": False}
    return {
        "ok": True,
        "referral_code": code,
        "referral_link": f"https://play.ponzi.land/r/{code}",
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--address", help="Optional wallet address to display referral code")
    args = ap.parse_args()

    print(LOGO)
    print("PonziClaw capabilities:")
    for i, c in enumerate(CAPABILITIES, 1):
        print(f"{i}. {c}")

    print("\nReferral rewards:")
    print("- Earn 20% of referred users' auctions for 2 weeks")

    referral = None
    if args.address:
        referral = fetch_referral(args.address)
        if referral.get("ok"):
            print(f"- Your referral code: {referral['referral_code']}")
            print(f"- Your referral link: {referral['referral_link']}")

    out = {
        "capabilities": CAPABILITIES,
        "referral_terms": "Earn 20% of referred users' auctions for 2 weeks",
    }
    if referral and referral.get("ok"):
        out["referral"] = referral

    print("\nJSON:")
    print(json.dumps(out, indent=2))
