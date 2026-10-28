import os
from dotenv import load_dotenv
from solders.pubkey import Pubkey

load_dotenv()

# =====================================================================
# QUANTITATIVE CONSTANTS & IMMUTABLE PARAMETERS
# =====================================================================
GAMMA_1 = 0.9975             # Pool 1 fee retention factor (0.25% fee)
GAMMA_2 = 0.9975             # Pool 2 fee retention factor (0.25% fee)
PHI = 0.0001                 # Kamino Flash Loan fee (0.01% / 1 bps)
MIN_NET_PROFIT_SOL = 0.00015 # Minimum net profit hurdle (~₹2.00 INR)
MIN_SPARK_SOL = 1.5          # Minimum swap size to qualify as a spark
SPARK_IMPACT_RATIO = 0.010   # 1.0% dislocation ratio trigger
SOL_INR_RATE = 13500.0       # ~₹13,500 / SOL
MIN_POOL_LIQUIDITY_USD = 5000.0 # Rejects scam / illiquid pools

# =====================================================================
# RPC ENDPOINTS (HELIUS DEDICATED AUTHENTICATED NETWORK)
# =====================================================================
HELIUS_API_KEY = os.getenv("HELIUS_API_KEY", "6e01a6b4-7dfb-409d-b314-7bdd99f1c03d").strip()
RPC_URL = os.getenv("RPC_URL", f"https://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}")
HELIUS_RPC_URL = RPC_URL
WSS_URL = f"wss://mainnet.helius-rpc.com/?api-key={HELIUS_API_KEY}"
FALLBACK_RPC_URL = os.getenv("FALLBACK_RPC_URL", "https://api.mainnet-beta.solana.com")

# =====================================================================
# SOLANA ON-CHAIN PROGRAM IDENTIFIERS & REAL KAMINO ACCOUNTS
# =====================================================================
KLEND_PROGRAM_ID = Pubkey.from_string("KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD")
KAMINO_MARKET_ID = Pubkey.from_string("7u3HeHxYDLhnCoErrtycNokbQYbWGzLs6JSDqGAv5PfF")
KAMINO_LMA_ID    = Pubkey.from_string("9DrvZvyWh1HuAoZxvYWMvkf2XCzryCpGgHqrMjyDWpmo")
KAMINO_SOL_RESERVE_ID = Pubkey.from_string("d4A2prbA2whesmvHaL88BH6Ewn5N4bTSU2Ze8P6Bc4Q")
KAMINO_SUPPLY_VAULT   = Pubkey.from_string("GafNuUXj9rxGLn4y79dPu6MHSuPWeJR6UtTWuexpGh3U")
KAMINO_FEE_RECEIVER   = Pubkey.from_string("3JNof8s453bwG5UqiXBLJc77NRQXezYYEBbk3fqnoKph")

RAYDIUM_AMM_PROGRAM_ID   = Pubkey.from_string("675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8")
RAYDIUM_CPMM_PROGRAM_ID  = Pubkey.from_string("CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C")
METEORA_DLMM_PROGRAM_ID  = Pubkey.from_string("LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo")
ORCA_WHIRLPOOL_PROGRAM_ID = Pubkey.from_string("whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc")
TOKEN_PROGRAM_ID         = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
ASSOCIATED_TOKEN_PROGRAM_ID = Pubkey.from_string("ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL")
SYSVAR_INSTRUCTIONS_ID   = Pubkey.from_string("Sysvar1nstructions1111111111111111111111111")
SYSTEM_PROGRAM_ID        = Pubkey.from_string("11111111111111111111111111111111")
SOL_MINT                 = Pubkey.from_string("So11111111111111111111111111111111111111112")
WSOL_STR                 = "So11111111111111111111111111111111111111112"

# Verified Anchor Discriminators for Kamino Flash Loan Instructions
KAMINO_FLASH_BORROW_DISCRIMINATOR = bytes([135, 231, 52, 167, 7, 52, 212, 193])
KAMINO_FLASH_REPAY_DISCRIMINATOR  = bytes([185, 117, 0, 203, 96, 245, 180, 186])

# Official Jito Mainnet Tip Accounts (Leader Auction Lane)
JITO_TIP_ACCOUNTS = [
    "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",
    "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
    "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",
    "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
    "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh",
    "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
    "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL",
    "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT"
]
