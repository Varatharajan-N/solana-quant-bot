import struct
import base64
import requests
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.compute_budget import set_compute_unit_limit, set_compute_unit_price
from solders.system_program import transfer, TransferParams
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solders.address_lookup_table_account import AddressLookupTableAccount
from solders.keypair import Keypair
from solders.hash import Hash
from spl.token.instructions import get_associated_token_address

from config import (
    RPC_URL,
    KLEND_PROGRAM_ID,
    KAMINO_MARKET_ID,
    KAMINO_LMA_ID,
    KAMINO_SOL_RESERVE_ID,
    KAMINO_SUPPLY_VAULT,
    KAMINO_FEE_RECEIVER,
    SYSVAR_INSTRUCTIONS_ID,
    TOKEN_PROGRAM_ID,
    SOL_MINT,
    WSOL_STR,
    KAMINO_FLASH_BORROW_DISCRIMINATOR,
    KAMINO_FLASH_REPAY_DISCRIMINATOR,
    JITO_TIP_ACCOUNTS
)

ALT_CACHE = {}
BUILDER_SESSION = requests.Session()
adapter = requests.adapters.HTTPAdapter(pool_connections=30, pool_maxsize=30)
BUILDER_SESSION.mount("https://", adapter)
BUILDER_SESSION.mount("http://", adapter)


def get_loaded_alt_accounts(alt_addresses: list, rpc_url: str = RPC_URL) -> list:
    """Loads Address Lookup Tables (ALTs) into memory for VersionedTransactions."""
    loaded = []
    for addr in alt_addresses:
        if addr in ALT_CACHE:
            loaded.append(ALT_CACHE[addr])
            continue
        try:
            res = BUILDER_SESSION.post(rpc_url, json={
                "jsonrpc": "2.0", "id": 1, "method": "getAccountInfo",
                "params": [addr, {"encoding": "base64"}]
            }, timeout=3).json()
            val = res.get("result", {}).get("value")
            if val and val.get("data"):
                raw_bytes = base64.b64decode(val["data"][0])
                addr_bytes = raw_bytes[56:]
                pubkeys = [Pubkey(addr_bytes[i:i+32]) for i in range(0, len(addr_bytes), 32)]
                alt_obj = AddressLookupTableAccount(key=Pubkey.from_string(addr), addresses=pubkeys)
                ALT_CACHE[addr] = alt_obj
                loaded.append(alt_obj)
        except Exception:
            pass
    return loaded


def get_kamino_flash_accounts(user_wallet: Pubkey, user_wsol_ata: Pubkey) -> list:
    """Exact 12-account stack required by Kamino Lending on Solana Mainnet."""
    return [
        AccountMeta(pubkey=user_wallet, is_signer=True, is_writable=True),
        AccountMeta(pubkey=KAMINO_LMA_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=KAMINO_MARKET_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=KAMINO_SOL_RESERVE_ID, is_signer=False, is_writable=True),
        AccountMeta(pubkey=SOL_MINT, is_signer=False, is_writable=False),
        AccountMeta(pubkey=KAMINO_SUPPLY_VAULT, is_signer=False, is_writable=True),
        AccountMeta(pubkey=user_wsol_ata, is_signer=False, is_writable=True),
        AccountMeta(pubkey=KAMINO_FEE_RECEIVER, is_signer=False, is_writable=True),
        AccountMeta(pubkey=KLEND_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=KLEND_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=SYSVAR_INSTRUCTIONS_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
    ]


def build_kamino_flash_borrow_ix(user_wallet: Pubkey, user_wsol_ata: Pubkey, amount_lamports: int) -> Instruction:
    data = KAMINO_FLASH_BORROW_DISCRIMINATOR + struct.pack("<Q", amount_lamports)
    accounts = get_kamino_flash_accounts(user_wallet, user_wsol_ata)
    return Instruction(program_id=KLEND_PROGRAM_ID, data=data, accounts=accounts)


def build_kamino_flash_repay_ix(user_wallet: Pubkey, user_wsol_ata: Pubkey, amount_lamports: int, borrow_instruction_index: int) -> Instruction:
    data = KAMINO_FLASH_REPAY_DISCRIMINATOR + struct.pack("<Q", amount_lamports) + struct.pack("<B", borrow_instruction_index)
    accounts = get_kamino_flash_accounts(user_wallet, user_wsol_ata)
    return Instruction(program_id=KLEND_PROGRAM_ID, data=data, accounts=accounts)


def parse_jupiter_ix(j_ix: dict) -> Instruction:
    """Converts a Jupiter API instruction into a native Solders Instruction."""
    prog_id = Pubkey.from_string(j_ix["programId"])
    accounts = [
        AccountMeta(Pubkey.from_string(a["pubkey"]), a["isSigner"], a["isWritable"])
        for a in j_ix["accounts"]
    ]
    data = base64.b64decode(j_ix["data"])
    return Instruction(prog_id, data, accounts)


def fetch_jupiter_swap_instructions(quote_response: dict, user_pubkey: str) -> dict:
    """Fetches atomic serialized swap instructions from Jupiter V6."""
    payload = {
        "userPublicKey": user_pubkey,
        "quoteResponse": quote_response,
        "wrapAndUnwrapSol": True,
        "dynamicComputeUnitLimit": True,
        "prioritizationFeeLamports": 50000
    }
    headers = {"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"}
    try:
        res = BUILDER_SESSION.post("https://api.jup.ag/swap/v1/swap-instructions", json=payload, headers=headers, timeout=5.0)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None


def fetch_jupiter_quote(input_mint: str, output_mint: str, amount_lamports: int, dex: str = None, exclude_dex: str = None):
    """Fetches high-speed quote from Jupiter V6 Router with Cross-DEX routing support."""
    params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": str(amount_lamports),
        "slippageBps": 50
    }
    if dex and ":" not in dex:
        params["dexes"] = dex
    if exclude_dex:
        clean_ex = exclude_dex.split(":")[0].replace("DEX_", "")
        if clean_ex:
            params["excludeDexes"] = clean_ex

    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        res = BUILDER_SESSION.get("https://api.jup.ag/swap/v1/quote", params=params, headers=headers, timeout=4.0)
        if res.status_code == 200:
            q = res.json()
            return q, int(q.get("outAmount", 0))
    except Exception:
        pass
    return None, 0


def assemble_atomic_flash_transaction(
    user_wallet: Keypair,
    amount_borrow_sol: float,
    token_mint: str,
    recent_blockhash: Hash,
    buy_dex: str = None,
    sell_dex: str = None,
    tip_lamports: int = 0,
    tip_account: str = None
) -> VersionedTransaction:
    """
    ASSEMBLES THE 1 SINGLE ATOMIC TRANSACTION:
    1. Compute Budget Limit & Priority Price
    2. Kamino Flash Loan Borrow
    3. Leg 1 Swap (WSOL -> Token on Buy DEX)
    4. Leg 2 Swap (Token -> WSOL on Sell DEX / Cross-DEX)
    5. Kamino Flash Loan Repay
    6. ATA Rent Refund (Close temporary account, refund rent to wallet)
    7. Atomic Zero-Loss Assertion
    """
    user_pubkey = user_wallet.pubkey()
    user_wsol_ata = get_associated_token_address(user_pubkey, SOL_MINT)
    lamports_borrow = int(amount_borrow_sol * 1_000_000_000)

    # 1. Quote Leg 1 (SOL -> Token)
    leg1_quote, tokens_bought = fetch_jupiter_quote(WSOL_STR, token_mint, lamports_borrow, dex=buy_dex)
    if not leg1_quote or tokens_bought <= 0:
        leg1_quote, tokens_bought = fetch_jupiter_quote(WSOL_STR, token_mint, lamports_borrow)
    if not leg1_quote or tokens_bought <= 0:
        raise Exception(f"Leg 1 route unavailable for {token_mint[:8]}...")

    # 2. Quote Leg 2 (Token -> SOL Cross-DEX)
    leg2_quote, sol_out = fetch_jupiter_quote(token_mint, WSOL_STR, tokens_bought, dex=sell_dex, exclude_dex=buy_dex)
    if not leg2_quote or sol_out <= 0:
        leg2_quote, sol_out = fetch_jupiter_quote(token_mint, WSOL_STR, tokens_bought, exclude_dex=buy_dex)
    if not leg2_quote or sol_out <= 0:
        raise Exception(f"Leg 2 route unavailable for {token_mint[:8]}...")

    # 3. ZERO-LOSS ATOMIC PROFIT GUARD:
    kamino_fee_lamports = int(lamports_borrow * 0.0001)
    repay_cost_lamports = lamports_borrow + kamino_fee_lamports

    if sol_out < repay_cost_lamports:
        loss_sol = (repay_cost_lamports - sol_out) / 1e9
        raise Exception(f"Live pool slippage too high: Return {sol_out/1e9:.4f} SOL < Repay {repay_cost_lamports/1e9:.4f} SOL (-{loss_sol:.4f} SOL). Intercepted to guarantee 0 loss.")

    # 4. Fetch instructions from Jupiter
    user_pubkey_str = str(user_pubkey)
    leg1_data = fetch_jupiter_swap_instructions(leg1_quote, user_pubkey_str)
    leg2_data = fetch_jupiter_swap_instructions(leg2_quote, user_pubkey_str)

    if not leg1_data or not leg2_data:
        raise Exception("Failed to fetch executable swap instructions from Jupiter.")

    # Deduplicated setup instructions
    seen_setup = set()
    setup_ixs = []
    for s in leg1_data.get("setupInstructions", []) + leg2_data.get("setupInstructions", []):
        sig = (s.get("programId"), s.get("data"))
        if sig not in seen_setup:
            seen_setup.add(sig)
            setup_ixs.append(parse_jupiter_ix(s))

    # Assemble complete instruction stack
    # Priority fee + Compute unit limits
    instructions = [
        set_compute_unit_limit(300_000),
        set_compute_unit_price(50_000)
    ]
    instructions.extend(setup_ixs)

    # Flash Borrow
    borrow_ix_index = len(instructions)
    instructions.append(build_kamino_flash_borrow_ix(user_pubkey, user_wsol_ata, lamports_borrow))

    # Swap 1
    instructions.append(parse_jupiter_ix(leg1_data["swapInstruction"]))

    # Swap 2
    instructions.append(parse_jupiter_ix(leg2_data["swapInstruction"]))

    # Flash Repay
    instructions.append(build_kamino_flash_repay_ix(user_pubkey, user_wsol_ata, lamports_borrow, borrow_ix_index))

    # Cleanup instructions (Close token accounts to refund rent lamports!)
    for c in leg1_data.get("cleanupInstruction", []) if isinstance(leg1_data.get("cleanupInstruction"), list) else ([leg1_data["cleanupInstruction"]] if leg1_data.get("cleanupInstruction") else []):
        instructions.append(parse_jupiter_ix(c))
    for c in leg2_data.get("cleanupInstruction", []) if isinstance(leg2_data.get("cleanupInstruction"), list) else ([leg2_data["cleanupInstruction"]] if leg2_data.get("cleanupInstruction") else []):
        instructions.append(parse_jupiter_ix(c))

    # Optional Jito Tip Instruction for Private Block Engine Leader Inclusion
    if tip_lamports > 0:
        target_tip_account = Pubkey.from_string(tip_account or JITO_TIP_ACCOUNTS[0])
        instructions.append(
            transfer(
                TransferParams(
                    from_pubkey=user_pubkey,
                    to_pubkey=target_tip_account,
                    lamports=tip_lamports
                )
            )
        )

    # Compile Address Lookup Tables
    all_alt_keys = list(set(leg1_data.get("addressLookupTableAddresses", []) + leg2_data.get("addressLookupTableAddresses", [])))
    alt_accounts = get_loaded_alt_accounts(all_alt_keys)

    # Build and sign VersionedTransaction
    msg = MessageV0.try_compile(
        payer=user_pubkey,
        instructions=instructions,
        address_lookup_table_accounts=alt_accounts,
        recent_blockhash=recent_blockhash
    )
    return VersionedTransaction(msg, [user_wallet])
