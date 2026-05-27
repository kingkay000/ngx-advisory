from sqlalchemy import text
from app.ngx_advisory_router import engine

def init_db():
    """Builds required engine relational infrastructure patterns inside SQLite file instance if absent."""
    with engine.connect() as conn:
        # 1. Buy Signals table layout
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ngx_buy_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                ticker TEXT NOT NULL,
                company TEXT,
                sector TEXT,
                signal TEXT NOT NULL DEFAULT 'BUY',
                hold_type TEXT,
                composite_score REAL,
                confidence TEXT,
                technical_score REAL,
                fundamental_score REAL,
                macro_score REAL,
                sentiment_score REAL,
                risk_score REAL,
                price_target REAL,
                stop_loss REAL,
                consensus_summary TEXT,
                dissenting_views TEXT,
                entry_guidance TEXT,
                review_trigger TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                UNIQUE(run_date, ticker)
            );
        """))

        # 2. Portfolio Advisory table layout
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ngx_portfolio_advisory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT NOT NULL,
                analysis_date TEXT NOT NULL,
                ticker TEXT NOT NULL,
                advisory TEXT NOT NULL DEFAULT 'HOLD',
                confidence TEXT,
                composite_score REAL,
                buy_price REAL,
                current_price REAL,
                pnl_pct REAL,
                key_risks TEXT,
                consensus_summary TEXT,
                review_trigger TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                UNIQUE(run_date, ticker)
            );
        """))

        # 3. Metadata Table layout
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ngx_run_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_date TEXT NOT NULL UNIQUE,
                macro_regime TEXT,
                macro_label TEXT,
                macro_regime_narrative TEXT,
                total_tickers_scanned INTEGER DEFAULT 0,
                buy_signals_count INTEGER DEFAULT 0,
                sell_signals_count INTEGER DEFAULT 0,
                hold_signals_count INTEGER DEFAULT 0,
                portfolio_hold_count INTEGER DEFAULT 0,
                portfolio_sell_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );
        """))

        # 4. API keys tracking schema
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS ngx_api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_hash TEXT NOT NULL UNIQUE,
                owner_name TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                last_used TEXT
            );
        """))
        conn.commit()