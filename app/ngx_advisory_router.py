import hashlib
import os
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

# ─────────────────────────────────────────────
# Database Connection (SQLite Engine Configured)
# ─────────────────────────────────────────────

NGX_DB_URL      = os.getenv("NGX_DB_URL", "sqlite:////app/data/ngx_advisory.db")
INTERNAL_TOKEN  = os.getenv("NGX_INTERNAL_TOKEN", "")

engine          = create_engine(
    NGX_DB_URL,
    connect_args={"check_same_thread": False},  # Essential for multi-threaded SQLite concurrency
    pool_pre_ping=True,
)
SessionLocal    = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─────────────────────────────────────────────
# Auth Dependencies
# ─────────────────────────────────────────────

def verify_api_key(
    x_api_key: str = Header(..., description="API key issued by NGX Advisory"),
    db: Session = Depends(get_db)
) -> str:
    """External API key verification for Zod / NGX Pulse readers."""
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    row = db.execute(
        text("SELECT owner_name FROM ngx_api_keys WHERE key_hash=:h AND is_active=1"),
        {"h": key_hash}
    ).fetchone()
    
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    
    try:
        db.execute(
            text("UPDATE ngx_api_keys SET last_used=datetime('now') WHERE key_hash=:h"),
            {"h": key_hash}
        )
        db.commit()
    except Exception:
        pass
        
    return row.owner_name


def verify_internal_token(
    x_internal_token: str = Header(..., description="Internal validation token for n8n script adjustments")
) -> bool:
    """Internal write credential check for incoming n8n automation payloads."""
    if not INTERNAL_TOKEN:
        raise HTTPException(status_code=503, detail="Internal token not configured on server engine environment")
    if x_internal_token != INTERNAL_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid internal transaction token authorization")
    return True


# ─────────────────────────────────────────────
# Pydantic Structural Models
# ─────────────────────────────────────────────

class BuySignalWrite(BaseModel):
    run_date:           str
    analysis_date:      str
    ticker:             str
    company:            Optional[str]   = None
    sector:             Optional[str]   = None
    signal:             str             = "BUY"
    hold_type:          Optional[str]   = None
    composite_score:    Optional[float] = None
    confidence:         Optional[str]   = None
    technical_score:    Optional[float] = None
    fundamental_score:  Optional[float] = None
    macro_score:        Optional[float] = None
    sentiment_score:    Optional[float] = None
    risk_score:         Optional[float] = None
    price_target:       Optional[float] = None
    stop_loss:          Optional[float] = None
    consensus_summary:  Optional[str]   = None
    dissenting_views:   Optional[str]   = None
    entry_guidance:     Optional[str]   = None
    review_trigger:     Optional[str]   = None


class PortfolioAdvisoryWrite(BaseModel):
    run_date:           str
    analysis_date:      str
    ticker:             str
    advisory:           str
    confidence:         Optional[str]   = None
    composite_score:    Optional[float] = None
    buy_price:          Optional[float] = None
    current_price:      Optional[float] = None
    pnl_pct:            Optional[float] = None
    key_risks:          Optional[str]   = None
    consensus_summary:  Optional[str]   = None
    review_trigger:     Optional[str]   = None


class RunMetadataWrite(BaseModel):
    run_date:                str
    macro_regime:            Optional[str] = None
    macro_label:             Optional[str] = None
    macro_regime_narrative:  Optional[str] = None
    total_tickers_scanned:   int           = 0
    buy_signals_count:       int           = 0
    sell_signals_count:      int           = 0
    hold_signals_count:      int           = 0
    portfolio_hold_count:    int           = 0
    portfolio_sell_count:    int           = 0


# ─────────────────────────────────────────────
# Router Endpoint Actions
# ─────────────────────────────────────────────

router = APIRouter()

@router.post("/internal/ngx/write/signal", include_in_schema=False)
def write_buy_signal(
    payload: BuySignalWrite,
    _: bool       = Depends(verify_internal_token),
    db: Session   = Depends(get_db)
):
    """Upsert a BUY signal row transaction from n8n pipeline iterations."""
    db.execute(text("""
        INSERT OR REPLACE INTO ngx_buy_signals
            (run_date, analysis_date, ticker, company, sector, signal, hold_type,
             composite_score, confidence, technical_score, fundamental_score,
             macro_score, sentiment_score, risk_score, price_target, stop_loss,
             consensus_summary, dissenting_views, entry_guidance, review_trigger,
             updated_at)
        VALUES
            (:run_date, :analysis_date, :ticker, :company, :sector, :signal, :hold_type,
             :composite_score, :confidence, :technical_score, :fundamental_score,
             :macro_score, :sentiment_score, :risk_score, :price_target, :stop_loss,
             :consensus_summary, :dissenting_views, :entry_guidance, :review_trigger,
             datetime('now'))
    """), payload.model_dump())
    db.commit()
    return {"status": "ok", "ticker": payload.ticker, "run_date": payload.run_date}


@router.post("/internal/ngx/write/advisory", include_in_schema=False)
def write_portfolio_advisory(
    payload: PortfolioAdvisoryWrite,
    _: bool       = Depends(verify_internal_token),
    db: Session   = Depends(get_db)
):
    """Upsert portfolio advisory items from running automation tasks."""
    db.execute(text("""
        INSERT OR REPLACE INTO ngx_portfolio_advisory
            (run_date, analysis_date, ticker, advisory, confidence, composite_score,
             buy_price, current_price, pnl_pct, key_risks, consensus_summary,
             review_trigger, updated_at)
        VALUES
            (:run_date, :analysis_date, :ticker, :advisory, :confidence, :composite_score,
             :buy_price, :current_price, :pnl_pct, :key_risks, :consensus_summary,
             :review_trigger, datetime('now'))
    """), payload.model_dump())
    db.commit()
    return {"status": "ok", "ticker": payload.ticker, "run_date": payload.run_date}


@router.post("/internal/ngx/write/metadata", include_in_schema=False)
def write_run_metadata(
    payload: RunMetadataWrite,
    _: bool       = Depends(verify_internal_token),
    db: Session   = Depends(get_db)
):
    """Upsert execution log parameters summary parameters validation records."""
    db.execute(text("""
        INSERT OR REPLACE INTO ngx_run_metadata
            (run_date, macro_regime, macro_label, macro_regime_narrative,
             total_tickers_scanned, buy_signals_count, sell_signals_count,
             hold_signals_count, portfolio_hold_count, portfolio_sell_count,
             updated_at)
        VALUES
            (:run_date, :macro_regime, :macro_label, :macro_regime_narrative,
             :total_tickers_scanned, :buy_signals_count, :sell_signals_count,
             :hold_signals_count, :portfolio_hold_count, :portfolio_sell_count,
             datetime('now'))
    """), payload.model_dump())
    db.commit()
    return {"status": "ok", "run_date": payload.run_date}


@router.get("/api/v1/ngx/advisory")
def get_latest_advisory(
    owner: str    = Depends(verify_api_key),
    db: Session   = Depends(get_db)
):
    """Fetch structured metrics from the latest successfully saved metrics run instance."""
    row = db.execute(
        text("SELECT run_date FROM ngx_run_metadata ORDER BY run_date DESC LIMIT 1")
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No advisory metadata sets available yet")
    return _build_advisory_response(row.run_date, db)


@router.get("/api/v1/ngx/advisory/{run_date}")
def get_advisory_by_date(
    run_date: str,
    owner: str    = Depends(verify_api_key),
    db: Session   = Depends(get_db)
):
    """Lookup specific date metric results."""
    try:
        parsed = datetime.strptime(run_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Target processing configuration date format must match YYYY-MM-DD")

    row = db.execute(
        text("SELECT run_date FROM ngx_run_metadata WHERE run_date=:d"),
        {"d": str(parsed)}
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"No tracked records located for historical marker date {run_date}")
    return _build_advisory_response(str(parsed), db)


@router.get("/api/v1/ngx/signals")
def get_buy_signals(
    run_date:  Optional[str]   = Query(None, description="YYYY-MM-DD — Defaults to newest tracking records"),
    sector:    Optional[str]   = Query(None, description="Target filter string for sector indexing"),
    min_score: Optional[float] = Query(None, description="Minimum acceptable asset health metric value"),
    owner: str                 = Depends(verify_api_key),
    db: Session                = Depends(get_db)
):
    """Fetch tracked buy triggers filtering items based on user query configurations."""
    target = _resolve_date(run_date, db)
    query  = "SELECT * FROM ngx_buy_signals WHERE run_date=:d"
    params = {"d": target}

    if sector:
        query += " AND sector=:sector"
        params["sector"] = sector
    if min_score is not None:
        query += " AND composite_score >= :min_score"
        params["min_score"] = min_score

    query += " ORDER BY composite_score DESC"
    rows = db.execute(text(query), params).fetchall()
    return {
        "run_date": target,
        "count":    len(rows),
        "signals":  [_row_to_dict(r) for r in rows]
    }


@router.get("/api/v1/ngx/portfolio")
def get_portfolio_advisory(
    run_date: Optional[str] = Query(None, description="YYYY-MM-DD — Defaults to the newest asset run parameters"),
    owner: str              = Depends(verify_api_key),
    db: Session             = Depends(get_db)
):
    """Fetch full portfolio items segregating holds from liquidation triggers."""
    target = _resolve_date(run_date, db)
    rows   = db.execute(
        text("SELECT * FROM ngx_portfolio_advisory WHERE run_date=:d ORDER BY advisory DESC, ticker"),
        {"d": target}
    ).fetchall()

    sells = [_row_to_dict(r) for r in rows if r.advisory == "SELL"]
    holds = [_row_to_dict(r) for r in rows if r.advisory == "HOLD"]

    return {
        "run_date":          target,
        "urgent_sell_count": len(sells),
        "hold_count":        len(holds),
        "urgent_sells":      sells,
        "holds":             holds
    }


@router.get("/api/v1/ngx/history")
def get_run_history(
    limit: int  = Query(10, ge=1, le=52, description="Maximum past run instances lookup limit metric counter"),
    owner: str  = Depends(verify_api_key),
    db: Session = Depends(get_db)
):
    """Fetch structural tracking history from historical database summary items logs."""
    rows = db.execute(
        text("""
            SELECT run_date, macro_regime, macro_label, total_tickers_scanned,
                   buy_signals_count, sell_signals_count, hold_signals_count,
                   portfolio_hold_count, portfolio_sell_count
            FROM   ngx_run_metadata
            ORDER  BY run_date DESC
            LIMIT  :limit
        """),
        {"limit": limit}
    ).fetchall()
    return {"count": len(rows), "runs": [_row_to_dict(r) for r in rows]}


# ─────────────────────────────────────────────
# Core Internal Utilities
# ─────────────────────────────────────────────

def _resolve_date(run_date: Optional[str], db: Session) -> str:
    if run_date:
        try:
            return str(datetime.strptime(run_date, "%Y-%m-%d").date())
        except ValueError:
            raise HTTPException(status_code=400, detail="Date configuration parameters must match YYYY-MM-DD template values")
    row = db.execute(
        text("SELECT run_date FROM ngx_run_metadata ORDER BY run_date DESC LIMIT 1")
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="No historical advisory sets are present within database registers")
    return row.run_date


def _row_to_dict(row) -> dict:
    d = dict(row._mapping)
    for k, v in d.items():
        if isinstance(v, date):
            d[k] = str(v)
    return d


def _build_advisory_response(target_date: str, db: Session) -> dict:
    meta = db.execute(
        text("SELECT * FROM ngx_run_metadata WHERE run_date=:d"),
        {"d": target_date}
    ).fetchone()

    signals   = db.execute(
        text("SELECT * FROM ngx_buy_signals WHERE run_date=:d ORDER BY composite_score DESC"),
        {"d": target_date}
    ).fetchall()

    portfolio = db.execute(
        text("SELECT * FROM ngx_portfolio_advisory WHERE run_date=:d ORDER BY advisory DESC, ticker"),
        {"d": target_date}
    ).fetchall()

    sells = [_row_to_dict(r) for r in portfolio if r.advisory == "SELL"]
    holds = [_row_to_dict(r) for r in portfolio if r.advisory == "HOLD"]

    return {
        "generated_at":           datetime.utcnow().isoformat() + "Z",
        "run_date":               target_date,
        "macro_regime":           meta.macro_regime            if meta else None,
        "macro_label":            meta.macro_label             if meta else None,
        "macro_regime_narrative": meta.macro_regime_narrative  if meta else None,
        "total_tickers_scanned":  meta.total_tickers_scanned   if meta else 0,
        "summary": {
            "buy_signals_count":     meta.buy_signals_count    if meta else len(signals),
            "sell_signals_count":    meta.sell_signals_count   if meta else 0,
            "hold_signals_count":    meta.hold_signals_count   if meta else 0,
            "portfolio_hold_count":  meta.portfolio_hold_count if meta else 0,
            "portfolio_sell_count":  meta.portfolio_sell_count if meta else 0,
        },
        "buy_signals":        [_row_to_dict(r) for r in signals],
        "portfolio_advisory": {
            "urgent_sell_count": len(sells),
            "hold_count":        len(holds),
            "urgent_sells":      sells,
            "holds":             holds
        }
    }