from collections import defaultdict
import time

class Metrics:
    def __init__(self):
        self.http_requests_total = defaultdict(int)
        self.webhook_requests_total = defaultdict(int)
        self.latency_buckets = {100: 0, 500: 0, float('inf'): 0}
        self.latency_sum = 0
        self.latency_count = 0

    def inc_http_request(self, path: str, status: int):
        self.http_requests_total[(path, str(status))] += 1

    def inc_webhook_result(self, result: str):
        self.webhook_requests_total[result] += 1

    def observe_latency(self, ms: float):
        self.latency_sum += ms
        self.latency_count += 1
        if ms <= 100:
            self.latency_buckets[100] += 1
        elif ms <= 500:
            self.latency_buckets[500] += 1
        else:
            self.latency_buckets[float('inf')] += 1

    def generate_output(self):
        lines = []
        
        lines.append("# HELP http_requests_total Total HTTP requests")
        lines.append("# TYPE http_requests_total counter")
        for (path, status), count in self.http_requests_total.items():
            lines.append(f'http_requests_total{{path="{path}",status="{status}"}} {count}')

        lines.append("# HELP webhook_requests_total Webhook processing outcomes")
        lines.append("# TYPE webhook_requests_total counter")
        for result, count in self.webhook_requests_total.items():
            lines.append(f'webhook_requests_total{{result="{result}"}} {count}')

        return "\n".join(lines)

metrics = Metrics()