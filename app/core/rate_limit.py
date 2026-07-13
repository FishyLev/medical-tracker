import time
from collections import defaultdict, deque
from fastapi import HTTPException, Request

class InMemoryRateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)

    def check(self, request: Request):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        bucket = self.requests[client_ip]

        while bucket and bucket[0] <= now - self.window_seconds:
            bucket.popleft()

        if len(bucket) >= self.max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        bucket.append(now)
