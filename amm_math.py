import math
from config import GAMMA_1, GAMMA_2, PHI, MIN_NET_PROFIT_SOL, MIN_SPARK_SOL, SPARK_IMPACT_RATIO, SOL_INR_RATE

# =====================================================================
# THE 5 QUANTITATIVE AMM FORMULAS (PURE NANOSECOND CPU REGISTERS)
# =====================================================================

def evaluate_spark(delta_sol_swap: float, pool_sol_reserve: float) -> bool:
    """
    FORMULA 1: The Golden Spark Condition.
    Guarantees swap is >= 1.5 SOL and shifts pool reserve by >= 1.0%.
    """
    if pool_sol_reserve <= 0:
        return False
    return (delta_sol_swap >= MIN_SPARK_SOL) and ((delta_sol_swap / pool_sol_reserve) >= SPARK_IMPACT_RATIO)


def determine_directionality(xa: float, ya: float, xb: float, yb: float):
    """
    FORMULA 2: In-Memory Cross-Product Directionality.
    Computes Left = xb * ya vs Right = xa * yb without floating point division.
    Returns:
        (x1, y1, x2, y2, buy_dex, sell_dex)
        Pool 1 = Buy Pool, Pool 2 = Sell Pool
    """
    left = xb * ya
    right = xa * yb

    if left > right:
        # DEX A is cheap (Buy on A), DEX B is expensive (Sell on B)
        return xa, ya, xb, yb, "DEX_A", "DEX_B"
    elif right > left:
        # DEX B is cheap (Buy on B), DEX A is expensive (Sell on A)
        return xb, yb, xa, ya, "DEX_B", "DEX_A"
    else:
        return None


def calculate_optimal_borrow(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    FORMULA 4: The Closed-Form AMM Calculus Optimal Sizing Equation.
    Solves for Delta x* where marginal profit dPi/dx = 0.
    Returns:
        delta_x_star in SOL, or 0.0 if marginal profit is negative.
    """
    # Numerator = sqrt((gamma1 * gamma2 * x1 * x2 * y1 * y2) / (1 + phi)) - (x1 * y2)
    num_root = math.sqrt((GAMMA_1 * GAMMA_2 * x1 * x2 * y1 * y2) / (1.0 + PHI))
    numerator = num_root - (x1 * y2)

    if numerator <= 0:
        return 0.0 # Spread cannot cover fees; zero-trade protection

    denominator = GAMMA_1 * (y2 + (GAMMA_2 * y1))
    delta_x_star = numerator / denominator

    # Guardrails: Minimum 0.05 SOL to cover gas, Cap at 1.0 SOL for safety
    return max(0.05, min(delta_x_star, 1.0))


def compute_expected_net_profit(x1: float, y1: float, x2: float, y2: float, delta_x: float):
    """
    Simulates exact AMM swap traversal across Leg 1 and Leg 2.
    Formula 5: Atomic Net Profit Settlement.
    """
    # Leg 1: SOL -> Token
    delta_y = (GAMMA_1 * y1 * delta_x) / (x1 + (GAMMA_1 * delta_x))
    # Leg 2: Token -> SOL
    delta_x_prime = (GAMMA_2 * x2 * delta_y) / (y2 + (GAMMA_2 * delta_y))

    # Repay Cost = delta_x * (1 + phi)
    repay_sol = delta_x * (1.0 + PHI)
    gas_deduction_sol = 0.00010 # Priority fee + base fee

    net_sol = delta_x_prime - repay_sol - gas_deduction_sol
    net_inr = net_sol * SOL_INR_RATE

    return delta_x_prime, repay_sol, net_sol, net_inr


def evaluate_hft_arbitrage(xa: float, ya: float, xb: float, yb: float, delta_sol_swap: float):
    """
    Full pipeline evaluator running in sub-microsecond CPU time.
    """
    # Step 1: Spark Filter
    if not evaluate_spark(delta_sol_swap, xa):
        return None, "SPARK_SUB_THRESHOLD"

    # Step 2: Directionality
    dir_res = determine_directionality(xa, ya, xb, yb)
    if not dir_res:
        return None, "BALANCED_PARITY"

    x1, y1, x2, y2, buy_dex, sell_dex = dir_res

    # Step 3: Friction Barrier (> 0.70% Gross Spread)
    price_ratio = (x2 * y1) / (x1 * y2)
    gross_spread_pct = (price_ratio - 1.0) * 100.0
    if gross_spread_pct <= 0.70:
        return None, f"SPREAD_TOO_TIGHT ({gross_spread_pct:.2f}%)"

    # Step 4: Optimal Sizing Calculus
    delta_x_star = calculate_optimal_borrow(x1, y1, x2, y2)
    if delta_x_star <= 0.0:
        return None, "MARGINAL_PROFIT_NEGATIVE"

    # Step 5: Hurdle Verification
    out_sol, repay_sol, net_sol, net_inr = compute_expected_net_profit(x1, y1, x2, y2, delta_x_star)

    if net_sol < MIN_NET_PROFIT_SOL:
        return None, f"NET_PROFIT_BELOW_HURDLE ({net_sol:.6f} SOL)"

    return {
        "buy_dex": buy_dex,
        "sell_dex": sell_dex,
        "borrow_sol": delta_x_star,
        "repay_sol": repay_sol,
        "out_sol": out_sol,
        "net_profit_sol": net_sol,
        "net_profit_inr": net_inr,
        "gross_spread_pct": gross_spread_pct
    }, "SUCCESS"
