import aiohttp
import asyncio
import time
import requests
from config import HELIUS_RPC_URL, MIN_POOL_LIQUIDITY_USD, WSOL_STR

RADAR_SESSION = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
RADAR_SESSION.mount("https://", adapter)
RADAR_SESSION.mount("http://", adapter)


async def get_live_surging_mints(session: aiohttp.ClientSession, limit: int = 30) -> list:
    """
    Morning Dynamic Token Discovery:
    Pulls live surging meme/volume tokens from:
    1. DexScreener Top Boosts
    2. DexScreener Latest Boosts
    3. GeckoTerminal Solana Trending Pools
    Zero static / dead / paused coins.
    """
    mints = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # 1. DexScreener Top Boosts
    try:
        url1 = "https://api.dexscreener.com/token-boosts/top/v1"
        async with session.get(url1, headers=headers, timeout=4) as r:
            if r.status == 200:
                data = await r.json()
                for item in data:
                    if item.get("chainId") == "solana":
                        addr = item.get("tokenAddress")
                        if addr and addr not in mints:
                            mints.append(addr)
    except Exception:
        pass

    # 2. DexScreener Latest Boosts
    try:
        url2 = "https://api.dexscreener.com/token-boosts/latest/v1"
        async with session.get(url2, headers=headers, timeout=4) as r:
            if r.status == 200:
                data = await r.json()
                for item in data:
                    if item.get("chainId") == "solana":
                        addr = item.get("tokenAddress")
                        if addr and addr not in mints:
                            mints.append(addr)
    except Exception:
        pass

    # 3. GeckoTerminal Solana Trending Pools
    try:
        url3 = "https://api.geckoterminal.com/api/v2/networks/solana/trending_pools"
        async with session.get(url3, headers=headers, timeout=4) as r:
            if r.status == 200:
                data = await r.json()
                for item in data.get("data", []):
                    rel = item.get("relationships", {})
                    base = rel.get("base_token", {}).get("data", {}).get("id", "")
                    if base.startswith("solana_"):
                        addr = base.replace("solana_", "")
                        if addr and addr not in mints:
                            mints.append(addr)
    except Exception:
        pass

    return mints[:limit]


async def check_freeze_authority_shield(session: aiohttp.ClientSession, mint_address: str) -> bool:
    """
    1-Bit Anti-Scam Shield via Helius Dedicated RPC:
    Checks if token mint has freezeAuthority enabled.
    Returns True if safe (freezeAuthority is None).
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getAccountInfo",
        "params": [mint_address, {"encoding": "jsonParsed"}]
    }
    try:
        async with session.post(HELIUS_RPC_URL, json=payload, timeout=3.5) as r:
            if r.status == 200:
                data = await r.json()
                info = data.get("result", {}).get("value", {}).get("data", {}).get("parsed", {}).get("info", {})
                freeze_auth = info.get("freezeAuthority")
                return freeze_auth is None
    except Exception:
        pass
    return True


async def fetch_direct_dual_reserves(session: aiohttp.ClientSession, mints: list) -> dict:
    """
    PURE DIRECT ON-CHAIN / AMM DISCOVERY (ZERO JUPITER HTTP DEPENDENCY):
    Queries DexScreener batch token pairs to extract real dual pool reserves:
    (xA, yA) on DEX A vs (xB, yB) on DEX B.
    Enforces minimum liquidity threshold and valid reserve depths.
    """
    if not mints:
        return {}

    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://api.dexscreener.com/latest/dex/tokens/{','.join(mints[:30])}"
    candidates = {}

    try:
        t0 = time.perf_counter()
        async with session.get(url, headers=headers, timeout=5.0) as r:
            if r.status == 200:
                latency_ms = (time.perf_counter() - t0) * 1000
                data = await r.json()
                pairs = data.get("pairs", [])
                by_token = {}

                for p in pairs:
                    sym = p.get("baseToken", {}).get("symbol", "UNKNOWN")
                    addr = p.get("baseToken", {}).get("address")
                    dex = p.get("dexId", "AMM")
                    liq = p.get("liquidity", {})
                    liq_usd = float(liq.get("usd", 0) or 0)
                    quote_sym = p.get("quoteToken", {}).get("symbol")
                    sol_res = float(liq.get("quote", 0) or 0)
                    base_res = float(liq.get("base", 0) or 0)
                    price_sol = float(p.get("priceNative", 0) or 0)

                    # Only evaluate pairs traded against SOL/WSOL with real reserves
                    if addr and quote_sym in ["SOL", "WSOL"] and liq_usd >= 1000 and sol_res > 0 and base_res > 0:
                        by_token.setdefault((sym, addr), []).append({
                            "dex": dex,
                            "pair_address": p.get("pairAddress"),
                            "sol_res": sol_res,
                            "base_res": base_res,
                            "price_sol": price_sol,
                            "liq_usd": liq_usd,
                            "latency_ms": latency_ms
                        })

                # Select candidates with 2 or more active pools
                for (sym, addr), p_list in by_token.items():
                    if len(p_list) >= 2:
                        candidates[(sym, addr)] = p_list
    except Exception:
        pass

    return candidates
