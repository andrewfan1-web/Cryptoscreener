
# CRYPTOSCREENER V6.3 — ANOMALOUS LEVERAGE ENGINE IMPLEMENTATION SCHEDULE

**APPROVED FOR IMPLEMENTATION**

> **AI INSTRUCTIONS**

- Do not summarize this contract; execute only the current phase.[^1]
- If a requested phase is incomplete, ask one clarifying question at most, then stop.[^1]
- When outputting files, preserve import compatibility with previously approved phases.[^1]
- Use a modular approach. Do not merge logic into single massive files.[^1]
- Do not redesign the architecture unless explicitly instructed by the user.[^1]
- Do not skip phases, merge phases, rename files, or introduce extra frameworks without approval.[^1]
- Output complete files only for the requested phase.[^1]
- Wait for user approval before continuing to the next phase.[^1]

This document is the single source of truth for the coding AI.[^1]
The AI must follow this schedule exactly.[^1]

### 0. CORE OBJECTIVE

Build a Telegram crypto screener that identifies **anomalous leverage expansion** in Bybit USDT perpetual markets.[^1]

The system must detect coins where:

- Open Interest is expanding in a statistically rare way for that specific coin.[^1]
- Volume is confirming or accelerating relative to that leverage expansion.[^1]
- BTC market regime is not actively hostile to long setups.[^1]
- The move is not already dangerously overextended on lower timeframes.[^1]

This is a screener.[^1]
It provides users with insights into crypto assets showing strong potential and, for qualified candidates, trader-readable execution context.[^1]
It must not place trades.[^1]
It must not connect to exchange accounts.[^1]
It must not become a portfolio tracker or execution bot.[^1]
It is a **long-only** idea-generation and context engine.

### Primary Data Stack

- Bybit V5 API for derivatives market data, funding, tickers, klines, and open interest.[^1]
- CoinGecko API for market cap and metadata.[^1]
- Telegram Bot API for alert delivery and interaction.[^1]
- Local file storage only for persistent history and state.[^1]


### Secondary Data Stack

- Coinalyze API, optional, config-gated, for non-primary enrichment only.
- Binance public endpoints, optional, config-gated, for fallback market data only when Bybit data is unavailable and only where the blueprint explicitly allows fallback behavior.


### Primary Design Principles

- Statistical anomaly detection first, not arbitrary score tuning.[^1]
- Modular architecture.[^1]
- Strong logging and state tracking.[^1]
- Local-only persistence.[^1]
- Strict control of AI drift.[^1]
- Keep the primary stack unchanged unless the user explicitly approves replacement.[^1]


### 1. NON-NEGOTIABLE IMPLEMENTATION RULES

1. The AI must implement phases sequentially.[^1]
2. The AI must not skip ahead.[^1]
3. The AI must not refactor earlier phases unless the current phase requires a necessary compatibility fix.[^1]
4. If a compatibility fix is required, the AI must clearly state why the fix is needed, which files are changed, and what behavior remains unchanged.[^1]
5. The AI must not create placeholder functions unless explicitly labeled TODO and approved by the user.[^1]
6. The AI must not introduce databases, Docker, Redis, Celery, FastAPI, cloud deployment, or any web UI unless explicitly requested.[^1]
7. If Telegram is implemented, use `python-telegram-bot` v20+ patterns only (`ApplicationBuilder`, `async/await`, `JobQueue`); do not use legacy `Updater` or `Dispatcher`.[^1]
8. The AI must use Python and a local VS Code workflow.[^1]
9. The AI must keep dependencies minimal.[^1]
10. All tests must be runnable offline with mocks; live API checks, if any, must be in clearly labeled smoke tests.[^1]
11. Runtime state files are allowed only at approved paths: `logs/state.json`, `logs/history.csv`, and `logs/cg_cache.json`.[^1]
12. The AI must preserve naming consistency across all modules.[^1]
13. For every computed feature in Phases 5–7, define formula, lookback window, units, null behavior, and rounding policy in code docstrings.[^1]
14. Preserve backward import compatibility with all previously approved phases.[^1]
15. `requirements.txt` is locked after Phase 1 unless the user explicitly approves a dependency change.[^1]
16. The AI must provide a short test procedure at the end of each phase.[^1]
17. The AI must not proceed to the next phase until the user replies with approval.[^1]
18. Do not use `time.sleep()` for orchestration. Scheduling must use `JobQueue`.[^1]
19. The screener and the risk engine must remain separate concerns. Do not merge them into one phase or one module.[^1]
20. The Z-Score engine must use the circular CSV history as the canonical long-lookback memory source.[^1]
21. No auto-trading, no order placement, no webhook execution.[^1]

### 2. LOCKED DIRECTORY STRUCTURE

The locked directory structure from V6.2 remains unchanged and no new top-level folders may be added without approval.[^1]
No file names may be changed after Phase 1 approval.[^1]

### 3. LOCKED EXTERNAL APIS

### Bybit V5 Public Endpoints

The primary Bybit public endpoints remain:

- `/v5/market/tickers?category=linear`[^1]
- `/v5/market/kline?category=linear`[^1]
- `/v5/market/open-interest?category=linear`[^1]


### Bybit fields expected from tickers

- `symbol`[^1]
- `lastPrice`[^1]
- `markPrice`[^1]
- `indexPrice`[^1]
- `openInterest`[^1]
- `openInterestValue`[^1]
- `turnover24h`[^1]
- `volume24h`[^1]
- `fundingRate`[^1]
- `price24hPcnt`[^1]


### Kline intervals required by this contract

- `15` for lower-timeframe structure.[^1]
- `60` for market regime and higher-timeframe context.[^1]


### CoinGecko endpoint

- `/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&sparkline=false&price_change_percentage=24h`[^1]


### CoinGecko fields required

- `id`[^1]
- `symbol`[^1]
- `name`[^1]
- `current_price`[^1]
- `market_cap`[^1]
- `market_cap_rank`[^1]
- `total_volume`[^1]
- `price_change_percentage_24h`[^1]

The AI must not replace these APIs without approval.[^1]
All timestamps must be normalized to UTC milliseconds.[^1]
Optional fallback handling is allowed, but the primary stack must remain unchanged.[^1]

### Secondary source usage policy

- Coinalyze may be used only as optional enrichment in later phases and must never replace Bybit as the primary market-data source.
- Binance may be used only as an optional fallback for kline continuity or outage resilience and must be disabled by default.
- Secondary sources must be controlled by explicit config flags.
- If secondary sources are unavailable, the primary workflow must still function.


### 4. STRATEGY LOGIC SPECIFICATION

This section defines the intended trading logic so later phases cannot drift.[^1]

### 4.1 Core Signal Concept

The bot is hunting **anomalous leverage expansion**.[^1]
Open Interest expansion must be statistically unusual for that specific coin.[^1]
Volume must confirm participation.[^1]
BTC market regime must not be actively hostile.[^1]
Alerts must avoid already overextended entries.[^1]

### 4.2 Timeframe Model

The system uses **dual timeframe logic**:

- **1h timeframe:** BTC market regime and higher-level context.[^1]
- **15m timeframe:** structure, ATR, EMA distance, swing low, local expansion behavior, and overextension state.[^1]

The system must not rely on 1h candles alone for entry-context features.[^1]
Quick Analysis summaries must use **1h regime context + 15m structure**, not 4h.

### 4.3 Canonical Z-Score Memory

All anomaly calculations that require historical normalization must use the local 30-day circular CSV history as the canonical memory source.[^1]

Minimum rules:

- If insufficient history exists, the engine must downgrade confidence and avoid promoting a coin to a high-confidence alert.[^1]
- Null handling must be explicit and documented.[^1]
- The canonical OI anomaly input is **per-cycle OI percentage change**, not raw OI level.
- Z-Score memory is coin-specific and must never be pooled across assets.


### 4.4 Locked anomaly definitions

- `oi_change_pct_15m = ((current_open_interest - prior_open_interest) / prior_open_interest) * 100`
- `oi_zscore_30d` must normalize the latest `oi_change_pct_15m` against that symbol’s 30-day CSV memory.
- `vol_oi_ratio = volume24h / open_interest_value`
- `vol_oi_zscore_30d` must normalize the latest `vol_oi_ratio` against that symbol’s 30-day CSV memory.
- `volume_zscore_30d` may normalize either `volume24h` or a documented short-horizon volume acceleration metric, but the implementation must be consistent and documented in the Phase 6 docstrings.
- Funding interpretation is contextual only; it may strengthen, weaken, or complicate a long anomaly, but it must not replace the OI anomaly requirement.


### 4.5 Alert Promotion Logic

A coin may be promoted to an alert only if:

- `oi_zscore_30d` is above the configured threshold.[^1]
- The asset passes universe filters.[^1]
- Regime logic does not block scanning.[^1]
- The overextension filter does not invalidate the setup.[^1]
- Cooldown and state rules allow a fresh alert.[^1]
- The setup is compatible with a **long-only** workflow.


### 4.6 Screener vs Risk Separation

- `features.py` and `scoring.py` decide whether a coin is interesting.[^1]
- `risk.py` provides contextual levels for a human trader.[^1]
- `risk.py` must not decide whether a coin enters the ranked universe.[^1]
- `scoring.py` must not fabricate trade levels.[^1]


### 5. PHASE-BY-PHASE BUILD SCHEDULE

The full 12-phase structure remains the same as V6.2, but the following revised clauses should replace the old ones where applicable.[^1]

### PHASE 1 — PROJECT FOUNDATION

Keep the original goal, allowed files, and minimal dependency set unchanged.[^1]

Add these config requirements:

- `COOLDOWN_REGIME_RESET: bool`
- `UNIVERSE_HARD_EXCLUDE_OVEREXTENDED: bool = False`
- `ENABLE_COINALYZE_ENRICHMENT: bool = False`
- `ENABLE_BINANCE_FALLBACK: bool = False`
- `COINGECKO_CACHE_TTL_SECONDS`
- `COINGECKO_CACHE_PATH = logs/cg_cache.json`
- `LONG_ONLY_MODE: bool = True`

Add these behavior requirements:

- `config.py` must provide explicit startup validation for required secrets and IDs before runtime boot.
- Validation failures must raise clear exceptions without printing sensitive values.
- `requirements.txt` must remain minimal unless the user explicitly approves an added dependency.[^1]


### PHASE 2 — RAW DATA CLIENTS

Keep Bybit and CoinGecko as the only mandatory clients in this phase.[^1]

Revise the CoinGecko cache requirement:

- CoinGecko client must implement a simple **5-minute file-backed cache** at `logs/cg_cache.json`, with in-memory reuse allowed during process lifetime.
- The cache must survive restarts.
- Cache reads must validate freshness using the configured TTL.

Add optional extensibility note:

- Do not implement Coinalyze or Binance in this phase unless the phase explicitly requests them later.


### PHASE 3 — SYMBOL MAPPING AND MERGED MARKET SNAPSHOT

No structural change.[^1]
Keep the merged snapshot scope limited to mapping and normalized asset assembly only.[^1]

### PHASE 4 — UNIVERSE FILTER

Keep the original filters and inclusion/exclusion output behavior.[^1]

Clarify overextension behavior:

- Overextension is **not** a hard exclusion by default in this phase.[^1]
- If `UNIVERSE_HARD_EXCLUDE_OVEREXTENDED` is enabled, the universe engine may exclude overextended assets and must return the exclusion reason explicitly.


### PHASE 5 — MARKET REGIME ENGINE

Keep the original BTC 1h regime rules unchanged.[^1]

Add transition-state support:

- The regime module must expose whether a regime transition occurred since the prior scan.
- This output will later support cooldown reset logic in Phase 9.


### PHASE 6 — FEATURE ENGINE

Keep the original feature list and deterministic feature-engine design.[^1]

Revise required anomaly fields:

- Replace ambiguous OI normalization language with explicit use of `oi_change_pct_15m` as the canonical OI anomaly input.
- `oi_change_15m` and `oi_change_1h` may still be stored in raw or percent terms if documented, but the Z-Score input must be fixed and unambiguous.
- `vol_oi_ratio` is locked as `volume24h / open_interest_value`.
- The feature engine must surface an explicit validity flag for insufficient 30-day memory.

Optional enrichment:

- If `ENABLE_COINALYZE_ENRICHMENT` is true, Coinalyze may enrich funding-context or supplementary derivatives context, but not replace primary features from Bybit.
- If enrichment is unavailable, the feature engine must continue with primary-stack data only.


### PHASE 7 — SCORING AND LABELING ENGINE

Keep the anomaly promotion framework, score breakdown, and configurable thresholds.[^1]

Revise labels to **long-only**:

- Allowed example labels:
    - `ANOMALOUS_LONG_BUILDUP`
    - `HIGH_OI_LOW_CONFIRMATION`
    - `OVEREXTENDED_ANOMALY`
    - `LOW_CONFIDENCE_REGIME`
    - `INSUFFICIENT_HISTORY`
- Remove short-side labels such as `ANOMALOUS_SHORT_BUILDUP`.

Rules:

- A bearish regime may downgrade or suppress long candidates, but must never produce a short trade label.
- Overextended setups may be downgraded or suppressed according to config.


### PHASE 8 — RISK CONTEXT ENGINE

Keep the original separation rule and human-context purpose.[^1]

Clarify scope:

- This phase is **long-only**.
- Stop loss, TP1, TP2, and invalidation logic are defined for bullish setups only.
- No bearish equivalent is required in this blueprint version.


### PHASE 9 — STATE AND CIRCULAR MEMORY

Keep the original persistence files `logs/history.csv` and `logs/state.json`.[^1]

Revise `history.csv` minimum columns to:

- `timestamp`
- `symbol`
- `price`
- `turnover24h`
- `volume24h`
- `open_interest`
- `open_interest_value`
- `funding_rate`
- `price_change_15m`
- `price_change_1h`
- `oi_change_15m`
- `oi_change_1h`
- `oi_change_pct_15m`
- `vol_oi_ratio`
- `regime`

Behavior rules:

- Append current metrics every scan cycle, default 15 minutes.[^1]
- Retain only the most recent 30 days.[^1]
- Prune rows older than the retention window automatically.[^1]
- The schema must be documented in the module docstring.[^1]
- Cooldown may reset on a favorable BTC regime transition if `COOLDOWN_REGIME_RESET` is enabled.
- State writes must be deterministic and restart-safe.[^1]


### PHASE 10 — TELEGRAM DELIVERY AND INTERACTION

Keep the original formatter, MarkdownV2, TradingView link, and inline-button requirements.[^1]

Revise Quick Analysis behavior:

- The callback must generate a compact **1h / 15m** summary using already available app modules.
- Do not introduce 4h candles.
- Do not introduce LLM summarization inside the bot unless explicitly requested.[^1]


### PHASE 11 — ORCHESTRATION LOOP

Keep the original loop order and `JobQueue` requirement unchanged.[^1]

Add one ordering clarification:

- Regime transition state must be available before state update so cooldown-reset logic can be applied deterministically during persistence.


### PHASE 12 — HARDENING AND QA

Keep the original bug-fix-only scope and final acceptance checks.[^1]

Add final hardening checks:

- Verify config validation blocks missing required secrets before loop startup.
- Verify `cg_cache.json` never stores secrets.
- Verify secondary-source failures degrade gracefully without breaking the primary path.


### 6. OUTPUT FORMAT RULES

Keep the original phase output format exactly:

1. Phase Title.[^1]
2. Files Created/Updated.[^1]
3. Full File Contents.[^1]
4. Short Explanation.[^1]
5. Exact Test Command(s).[^1]
6. STOP and wait for approval.[^1]

No snippets unless explicitly requested.[^1]
No pseudo-code unless explicitly requested.[^1]
No next-phase preview unless the user asks.[^1]

### 7. DRIFT PREVENTION RULES

Keep all original drift-prevention rules and add these clarifications:

- Do not remove the 30-day circular CSV memory requirement.[^1]
- Do not downgrade 15m structure analysis back to 1h-only logic.[^1]
- Do not replace the OI anomaly requirement with arbitrary scoring-only logic.[^1]
- Do not introduce short-trade labeling or short-side risk logic in this version.
- Do not replace the primary Bybit/CoinGecko stack with Coinalyze or Binance.[^1]
- Do not use private Bybit endpoints or signing logic.[^1]
- Do not use `time.sleep()` for scan orchestration.[^1]


