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
    ASSOCIATED_TOKEN_PROGRAM_ID,
    SOL_MINT,
    WSOL_STR,
    JITO_TIP_ACCOUNTS
)


def get_associated_token_address(wallet_address: Pubkey, token_mint_address: Pubkey) -> Pubkey:
    """Pure Solders implementation of SPL Associated Token Address derivation."""
    ata, _ = Pubkey.find_program_address(
        [bytes(wallet_address), bytes(TOKEN_PROGRAM_ID), bytes(token_mint_address)],
        ASSOCIATED_TOKEN_PROGRAM_ID
    )
    return ata


def assemble_atomic_execution_transaction(
    user_wallet: Keypair,
    recent_blockhash: Hash,
    tip_lamports: int = 10_000,
    tip_account_str: str = None
) -> VersionedTransaction:
    """
    Constructs the Single Atomic Execution Transaction:
    - 0 External HTTP dependencies (Zero Jupiter API).
    - Compute Budget Limit (150,000 CU) & Priority Price (25,000 micro-lamports).
    - Jito Validator Leader Auction Tip.
    - Fits under standard Solana MTU.
    """
    user_pubkey = user_wallet.pubkey()
    tip_target = Pubkey.from_string(tip_account_str or JITO_TIP_ACCOUNTS[0])

    instructions = [
        set_compute_unit_limit(150_000),
        set_compute_unit_price(25_000),
        transfer(TransferParams(
            from_pubkey=user_pubkey,
            to_pubkey=tip_target,
            lamports=max(10_000, tip_lamports)
        ))
    ]

    msg = MessageV0.try_compile(
        payer=user_pubkey,
        instructions=instructions,
        address_lookup_table_accounts=[],
        recent_blockhash=recent_blockhash
    )
    return VersionedTransaction(msg, [user_wallet])
