import hmac
import hashlib
import time
import uuid
from fastapi import FastAPI, Request, Header, Response
from fastapi.responses import JSONResponse, PlainTextResponse

# DELETED: from starlette.middleware.base import BaseMiddleware (The source of your error)

from app.config import settings
from app.models import WebhookPayload
from app.storage import init_db, insert_message, get_messages, get_stats
from app.logging_utils import logger
from app.metrics import metrics

# Initialize DB on startup
try:
    init_db()
except Exception as e:
    logger.error(f"DB Init Failed: {e}")

app = FastAPI()

# --- REPLACEMENT MIDDLEWARE (No Import Required) ---
@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    # Process the request
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000
    
    # Log Context
    log_extra = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "latency_ms": round(process_time, 2)
    }
    
    # If webhook specific context exists in request state, add it
    if hasattr(request.state, "webhook_log"):
        log_extra.update(request.state.webhook_log)

    logger.info("request_processed", extra=log_extra)
    metrics.inc_http_request(request.url.path, response.status_code)
    metrics.observe_latency(process_time)
    
    return response
# ---------------------------------------------------

@app.post("/webhook")
async def webhook(
    request: Request,
    x_signature: str = Header(None, alias="X-Signature")
):
    # 1. Signature Validation
    if not x_signature:
        metrics.inc_webhook_result("invalid_signature")
        logger.error("Missing Signature")
        return JSONResponse(status_code=401, content={"detail": "invalid signature"})

    body_bytes = await request.body()
    
    # Compute expected signature
    expected_sig = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        body_bytes,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(x_signature, expected_sig):
        metrics.inc_webhook_result("invalid_signature")
        logger.error("Invalid Signature Mismatch")
        return JSONResponse(status_code=401, content={"detail": "invalid signature"})

    # 2. Parse & Validate Payload
    try:
        json_body = await request.json()
        payload = WebhookPayload(**json_body)
    except Exception as e:
        metrics.inc_webhook_result("validation_error")
        logger.error(f"Validation Error: {e}")
        return JSONResponse(status_code=422, content={"detail": str(e)})

    # 3. Persistence & Idempotency
    data = payload.model_dump(by_alias=True)
    is_new = insert_message(data)
    
    result = "created" if is_new else "duplicate"
    metrics.inc_webhook_result(result)

    # Attach to request state for the Middleware logger to pick up
    request.state.webhook_log = {
        "message_id": payload.message_id,
        "dup": not is_new,
        "result": result
    }

    return {"status": "ok"}

# Wrapper to handle 'from' query param
@app.get("/messages")
async def list_messages_wrapper(request: Request, limit: int = 50, offset: int = 0, since: str = None, q: str = None):
    from_param = request.query_params.get("from")
    data, total = get_messages(limit, offset, from_param, since, q)
    return {
        "data": data,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/stats")
def get_stats_endpoint():
    return get_stats()

@app.get("/metrics")
def get_metrics():
    return PlainTextResponse(metrics.generate_output())

@app.get("/health/live")
def health_live():
    return {"status": "ok"}

@app.get("/health/ready")
def health_ready():
    try:
        get_stats() 
        if not settings.WEBHOOK_SECRET:
            raise Exception("Secret missing")
        return {"status": "ok"}
    except:
        return Response(status_code=503)