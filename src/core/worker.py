import os
from arq.connections import RedisSettings
from src.models.drift_monitor import DriftMonitor
from src.security.alerts import trigger_security_alert

drift_monitor = DriftMonitor()

async def check_drift(ctx, text: str, prediction: str):
    """Background task to check for model drift."""
    drift_monitor.check([text], [prediction])

async def send_security_alert(ctx, alert_type: str, result: dict):
    """Background task to send a security alert."""
    trigger_security_alert(alert_type, result)

class WorkerSettings:
    """ARQ Worker configuration"""
    functions = [check_drift, send_security_alert]
    redis_settings = RedisSettings(host=os.getenv('REDIS_HOST', 'localhost'), port=6379)
