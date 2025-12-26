import time
import hmac
import hashlib
import logging
import uuid
from fastapi import FastAPI, Request, HTTPException, Depends, Header, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from . import config, logging_utils, models, storage, metrics

logging_utils.setup_logging(config.settings.LOG_LEVEL)
logger = logging.getLogger(__name__)
storage.init_db()

app = FastAPI()

@app.middleware("http")
async def log_and_measure_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    
    metrics.HTTP_REQUESTS_TOTAL.labels(
        method=request.method, 
        path=request.url.path, 
        status=response.status_code
    ).inc()
    metrics.REQUEST_LATENCY.observe(process_time)

    log_data = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "latency_ms": round(process_time, 2)
    }
    if hasattr(request.state, "log_extra"):
        log_data.update(request.state.log_extra)

    logger.info("request_processed", extra=log_data)
    return response

async def verify_signature(request: Request):
    """
    Validates X-Signature against HMAC-SHA256(secret, raw_body).
    """
    signature = request.headers.get("X-Signature")
    if not signature:
        metrics.WEBHOOK_REQUESTS_TOTAL.labels(result="invalid_signature").inc()
        raise HTTPException(status_code=401, detail="invalid signature")

    body = await request.body()
    secret = config.settings.WEBHOOK_SECRET.encode()
    
    computed_sig = hmac.new(secret, body, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(computed_sig, signature):
        metrics.WEBHOOK_REQUESTS_TOTAL.labels(result="invalid_signature").inc()
        raise HTTPException(status_code=401, detail="invalid signature")
    
    return True


@app.post("/webhook", status_code=200)
async def receive_webhook(
    request: Request,
    response: Response,
    verified: bool = Depends(verify_signature),
    db: Session = Depends(storage.get_db)
):
    try:
        payload_data = await request.json()
        payload = models.WebhookPayload(**payload_data)
    except Exception as e:
        metrics.WEBHOOK_REQUESTS_TOTAL.labels(result="validation_error").inc()
        request.state.log_extra = {"result": "validation_error"}
        raise HTTPException(status_code=422, detail=str(e))

    inserted = storage.insert_message(db, payload)
    
    if inserted:
        result_status = "created"
    else:
        result_status = "duplicate"

    metrics.WEBHOOK_REQUESTS_TOTAL.labels(result=result_status).inc()
    
    request.state.log_extra = {
        "message_id": payload.message_id, 
        "dup": not inserted,
        "result": result_status
    }
    
    return {"status": "ok"}

@app.get("/messages")
def list_messages(
    limit: int = 50, 
    offset: int = 0, 
    from_: str | None = None,
    since: str | None = None,
    q: str | None = None,
    db: Session = Depends(storage.get_db)
):
    since_dt = None
    if since:
        try:
            since_dt = models.datetime.fromisoformat(since.replace('Z', '+00:00'))
        except ValueError:
             raise HTTPException(status_code=422, detail="Invalid date format")

    results, total = storage.get_messages(db, limit, offset, from_, since_dt, q)
    
    data = [
        models.MessageResponse(
            message_id=msg.message_id,
            from_=msg.from_msisdn,
            to=msg.to_msisdn,
            ts=msg.ts,
            text=msg.text
        ) for msg in results
    ]
    
    return {
        "data": data,
        "meta": {
            "total": total,
            "limit": limit,
            "offset": offset
        }
    }

@app.get("/stats")
def get_stats(db: Session = Depends(storage.get_db)):
    return storage.get_stats_data(db)

@app.get("/health/live")
def liveness():
    return {"status": "ok"}

@app.get("/health/ready")
def readiness(db: Session = Depends(storage.get_db)):
    if not config.settings.WEBHOOK_SECRET:
        return JSONResponse(status_code=503, content={"detail": "WEBHOOK_SECRET not set"})
    
    try:
        db.execute(models.select(1)).scalar()
    except Exception:
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})
        
    return {"status": "ready"}

@app.get("/metrics")
def metrics_endpoint():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)