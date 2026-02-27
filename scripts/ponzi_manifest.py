#!/usr/bin/env python3
import json
import os
from pathlib import Path
from typing import Dict, Any

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TOKENS_PATH = BASE_DIR / "references" / "mainnet.tokens.json"
DEFAULT_MANIFEST_PATH = BASE_DIR / "references" / "manifest_mainnet.json"


def load_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_tokens_config() -> Dict[str, Any]:
    p = Path(os.getenv("PONZI_TOKENS_CONFIG", str(DEFAULT_TOKENS_PATH)))
    return load_json(p)


def load_manifest() -> Dict[str, Any]:
    p = Path(os.getenv("PONZI_MANIFEST_PATH", str(DEFAULT_MANIFEST_PATH)))
    return load_json(p)


def token_map_by_address() -> Dict[str, Dict[str, Any]]:
    cfg = load_tokens_config()
    out: Dict[str, Dict[str, Any]] = {}
    for t in cfg.get("availableTokens", []):
        addr = str(t.get("address", "")).lower()
        if addr:
            out[addr] = t
    return out


def token_symbol(addr: str) -> str:
    m = token_map_by_address()
    t = m.get(str(addr).lower())
    if t:
        return t.get("symbol", addr)
    return addr


def actions_contract_address() -> str:
    mf = load_manifest()
    for c in mf.get("contracts", []):
        if c.get("tag") == "ponzi_land-actions":
            return c["address"]
        abi = c.get("abi", [])
        for item in abi:
            if isinstance(item, dict) and item.get("interface_name") == "ponzi_land::systems::actions::IActions":
                return c["address"]
    raise RuntimeError("Could not find ponzi_land-actions in manifest")
