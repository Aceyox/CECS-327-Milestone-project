from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

app = FastAPI(title="Disaster Alert System - Admin API")


alerts = []

class Alert(BaseModel):
    message: str
    severity: str

@app.post("/send_alert")
def send_alert(alert: Alert):
    """Admin sends a new alert."""
    alert_entry = {
        "message": alert.message,
        "severity": alert.severity,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    alerts.append(alert_entry)
    return {"status": "Alert sent successfully", "alert": alert_entry}

@app.get("/get_status")
def get_status():
    """Client checks current alert status."""
    if not alerts:
        return {"status": "No active alerts"}
    return {
        "status": "Active",
        "latest_alert": alerts[-1],
        "total_alerts": len(alerts)
    }
