import logging
import json
import time
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
        if hasattr(record, "method"):
            log_record["method"] = record.method
        if hasattr(record, "path"):
            log_record["path"] = record.path
        if hasattr(record, "status"):
            log_record["status"] = record.status
        if hasattr(record, "latency_ms"):
            log_record["latency_ms"] = record.latency_ms
        
        if hasattr(record, "message_id"):
            log_record["message_id"] = record.message_id
        if hasattr(record, "dup"):
            log_record["dup"] = record.dup
        if hasattr(record, "result"):
            log_record["result"] = record.result

        return json.dumps(log_record)

def setup_logger(level="INFO"):
    logger = logging.getLogger("lyftr_app")
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger

logger = setup_logger()