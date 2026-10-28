# 🏛️ THE FINAL ONE : Solana Wall Street HFT Arbitrage Engine

A high-frequency trading (HFT) quantitative arbitrage engine for the Solana blockchain.
Built on the **Morning 5-Formula AMM Calculus Strategy**, **Dynamic Surge Radar (Zero Static Coins)**, **Helius Authenticated RPC Network**, and **Kamino Zero-Capital Flash Loans** with **Private Jito Bundles**.

---

## 📁 System Architecture (`D:\THE FINAL ONE`)

| File | Purpose |
|---|---|
| **[`.env`](file:///D:/THE%20FINAL%20ONE/.env)** | Helius RPC API key, Wallet address (`6w5w...7EVV`), and base58 private key |
| **[`config.py`](file:///D:/THE%20FINAL%20ONE/config.py)** | Quantitative constants, fee matrix, Kamino program IDs, and Jito tip accounts |
| **[`amm_math.py`](file:///D:/THE%20FINAL%20ONE/amm_math.py)** | Pure nanosecond AMM calculus engine (The 5 Golden Formulas) |
| **[`radar.py`](file:///D:/THE%20FINAL%20ONE/radar.py)** | Dynamic event-driven surge discovery (Top boosts, Latest boosts, GeckoTerminal) & 1-bit on-chain freeze shield |
| **[`atomic_builder.py`](file:///D:/THE%20FINAL%20ONE/atomic_builder.py)** | Kamino flash loan borrow/repay assembler, Jupiter instruction parser, ATA auto-closing rent refund |
| **[`executor.py`](file:///D:/THE%20FINAL%20ONE/executor.py)** | Keypair signer, multi-region Jito bundle broadcaster, SVM pre-flight simulation shield |
| **[`main.py`](file:///D:/THE%20FINAL%20ONE/main.py)** | Production runner supporting `--mode paper` and `--mode live` with embedded auto-refresh web dashboard |
| **[`test_bot.py`](file:///D:/THE%20FINAL%20ONE/test_bot.py)** | 5-step comprehensive pre-flight diagnostic suite |

---

## ⚡ The 5 Morning Quantitative Formulas

1. **Formula 1: Golden Spark Condition**
   $$\Delta \text{SOL}_{\text{swap}} \ge 1.5 \quad \text{and} \quad \frac{\Delta \text{SOL}_{\text{swap}}}{R_{\text{pool}}} \ge 1.0\%$$
   Filters out retail noise; only triggers when a swap dislocates pool reserves.

2. **Formula 2: In-Memory Cross-Product Directionality**
   $$\text{Left} = x_B \cdot y_A \quad \text{vs} \quad \text{Right} = x_A \cdot y_B$$
   Determines the cheapest buy pool and most expensive sell pool in $0.001 \text{ ms}$ without floating point division.

3. **Formula 3: Friction Barrier**
   $$S_{\text{gross}} = \left(\frac{x_B \cdot y_A}{x_A \cdot y_B} - 1\right) > 0.70\%$$
   Rejects spreads that cannot overcome Raydium/Orca fees $(2 \times 0.25\%)$ and Kamino flash loan fee $(0.01\%)$.

4. **Formula 4: Closed-Form Optimal Borrow Calculus**
   $$\Delta x^* = \frac{\sqrt{\frac{\gamma_1 \gamma_2 x_1 x_2 y_1 y_2}{1 + \phi}} - x_1 y_2}{\gamma_1 (y_2 + \gamma_2 y_1)}$$
   Mathematically calculates the exact flash loan borrow amount in SOL that maximizes net profit while eliminating self-slippage.

5. **Formula 5: Zero-Loss Assertion & Minimum Net Hurdle**
   $$\Delta x'' - \Delta x(1 + \phi) - \text{Gas} \ge +0.00015 \text{ SOL} \quad (\sim\text{₹}2.00 \text{ INR})$$
   Enforced in both CPU memory and on-chain instructions. If slippage occurs, the transaction reverts with $0$ capital loss.

---

## 🛠️ How to Run

### 1. Run Pre-flight Diagnostic Check
```powershell
cd "D:\THE FINAL ONE"
python test_bot.py
```

### 2. Run Paper Trading Mode (Simulation Fills)
```powershell
python main.py --mode paper --duration 600
```
*(Runs for 10 minutes, streams live trades to terminal & saves `trade_history_log.json`)*

### 3. Run Live On-Chain Mode (Real Jito Bundles + Flash Loans)
```powershell
python main.py --mode live
```
*(Broadcasts directly to Jito Block Engine & Helius SWQoS with 0-loss SVM simulation guard)*

### 4. Live Browser Dashboard
View real-time auto-refresh terminal logs in your browser at:
`http://localhost:10000`
