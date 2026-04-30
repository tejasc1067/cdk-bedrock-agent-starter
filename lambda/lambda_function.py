import json
import os
from datetime import datetime, timezone, timedelta


def lambda_handler(event, context):
    tz_name = os.environ.get("TZ_NAME", "IST")
    tz_hours = int(os.environ.get("TZ_OFFSET_HOURS", 5))
    tz_minutes = int(os.environ.get("TZ_OFFSET_MINUTES", 30))

    tz = timezone(timedelta(hours=tz_hours, minutes=tz_minutes))
    now = datetime.now(tz)

    sign = "+" if tz_hours >= 0 else ""
    offset_str = f"UTC{sign}{tz_hours}:{abs(tz_minutes):02d}"

    body = {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "timezone": f"{tz_name} ({offset_str})",
        "datetime_iso": now.isoformat(),
    }

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup", ""),
            "apiPath": event.get("apiPath", ""),
            "httpMethod": event.get("httpMethod", ""),
            "httpStatusCode": 200,
            "responseBody": {
                "application/json": {
                    "body": json.dumps(body)
                }
            },
        },
    }
