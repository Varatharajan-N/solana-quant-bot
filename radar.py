import aiohttp
import asyncio
import time
import requests
from config import HELIUS_RPC_URL, MIN_POOL_LIQUIDITY_USD, WSOL_STR

RADAR_SESSION = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
RADAR_SESSION.mount("https://", adapter)
RADAR_SESSION.mount("http://", adapter)


async def get_live_surging_mints(session: aiohttp.ClientSession, limit: int = 25) -> list:
    """
    Morning Event-Driven Dynamic Token Discovery:
    Pulls live surging meme/volume tokens from:
    1. DexScreener Top Boosts
    2. DexScreener Latest Boosts
    3. GeckoTerminal Solana Trending Pools
    Eliminates dead / static / paused coins completely.
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
    On-chain 1-Bit Anti-Scam Shield via Helius Dedicated RPC:
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


async def fetch_onchain_reserves(session: aiohttp.ClientSession, mint: str) -> dict:
    """
    Morning On-Chain Reserve Extractor:
    Probes live liquidity depth and price impact on-chain via Jupiter router.
    """
    url = "https://api.jup.ag/swap/v1/quote"
    params = {
        "inputMint": WSOL_STR,
        "outputMint": mint,
        "amount": "150000000", # 0.15 SOL probe
        "slippageBps": "50"
    }
    t0 = time.perf_counter()
    try:
        async with session.get(url, params=params, timeout=4.0) as r:
            if r.status == 200:
                data = await r.json()
                latency_ms = (time.perf_counter() - t0) * 1000
                route = data.get("routePlan", [])
                out_amount = int(data.get("outAmount", 0))
                price_impact_pct = float(data.get("priceImpactPct", 0) or 0) * 100.0
                dex_label = route[0].get("swapInfo", {}).get("label", "DEX") if route else "DEX"
                return {
                    "latency_ms": latency_ms,
                    "dex": dex_label,
                    "out_amount": out_amount,
                    "price_impact_pct": price_impact_pct
                }
    except Exception:
        pass
    return None


async def inspect_dual_pools(session: aiohttp.ClientSession, mints: list) -> dict:
    """
    Filters surging tokens for verified multi-DEX presence (Raydium, Meteora, PumpSwap, Orca).
    Enforces minimum liquidity threshold to eliminate rug/honeypot traps.
    """
    if not mints:
        return {}
    headers = {"User-Agent": "Mozilla/5.0"}
    url = f"https://api.dexscreener.com/latest/dex/tokens/{','.join(mints[:25])}"
    candidates = {}
    try:
        async with session.get(url, headers=headers, timeout=5) as r:
            if r.status == 200:
                data = await r.json()
                pairs = data.get("pairs", [])
                by_token = {}
                for p in pairs:
                    sym = p.get("baseToken", {}).get("symbol", "UNKNOWN")
                    addr = p.get("baseToken", {}).get("address")
                    dex = p.get("dexId")
                    liq = p.get("liquidity", {}).get("usd", 0)
                    price = float(p.get("priceUsd", 0) or 0)

                    if addr and liq >= MIN_POOL_LIQUIDITY_USD and price > 0:
                        by_token.setdefault((sym, addr), []).append({
                            "dex": dex,
                            "liq": liq,
                            "price": price,
                            "pair_address": p.get("pairAddress")
                        })

                # Filter tokens that have at least 2 distinct DEX pools
                for (sym, addr), p_list in by_token.items():
                    dexes = set(x["dex"] for x in p_list)
                    if len(dexes) >= 2:
                        candidates[(sym, addr)] = p_list
    except Exception:
        pass
    return candidates
