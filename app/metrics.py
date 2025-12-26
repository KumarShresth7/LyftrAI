from prometheus_client import Counter, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"]
)

WEBHOOK_REQUESTS_TOTAL = Counter(
    "webhook_requests_total",
    "Webhook processing outcomes",
    ["result"]
)

REQUEST_LATENCY = Histogram(
    "request_latency_ms",
    "Request latency in milliseconds",
    buckets=(100, 500, float("inf"))
)