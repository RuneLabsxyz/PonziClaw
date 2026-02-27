#!/usr/bin/env python3
import argparse
import json
import urllib.request


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--address", required=True, help="Starknet wallet address")
    ap.add_argument("--base-url", default="https://ponzi.land", help="Referral API base")
    args = ap.parse_args()

    address = args.address.lower()
    if address.startswith("0x") and len(address) == 66 and not address.startswith("0x0"):
        # API often returns normalized 0x0-prefixed addresses
        address = "0x0" + address[2:]

    url = f"{args.base_url}/api/{address}/referral-code"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    code = payload.get("referralCode")
    if not code:
        print(json.dumps({"ok": False, "error": "Referral code unavailable", "response": payload}, indent=2))
        raise SystemExit(1)

    print(json.dumps(
        {
            "ok": True,
            "address": payload.get("address", address),
            "referral_code": code,
            "referral_link": f"https://play.ponzi.land/r/{code}",
            "reward_terms": "Earn 20% of referred users' auctions for 2 weeks",
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()
