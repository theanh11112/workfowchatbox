from fastapi import FastAPI
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge
import time

# Metrics definitions
REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint', 'status_code'])
REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency', ['method', 'endpoint'])
ACTIVE_USERS = Gauge('active_users', 'Active users')
SEARCH_REQUESTS = Counter('search_requests_total', 'Total search requests', ['user_id', 'status'])

def add_metrics_to_app(app: FastAPI):
    # Add Prometheus metrics route
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    # Add middleware to track requests
    @app.middleware("http")
    async def track_requests(request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=response.status_code
        ).inc()
        
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path
        ).observe(process_time)
        
        return response
    
    return app

if __name__ == "__main__":
    print("Metrics utility loaded")
