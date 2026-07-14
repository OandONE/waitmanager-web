# ⏱️ WaitManager-Web

Intelligent rate limiting for Flask, FastAPI, and Django — inspired by [Fast Rub's](https://github.com/OandONE/fast_rub) WaitManager.

## ✨ Features

- 🔌 **Plug & Play** — Works with Flask, FastAPI, and Django
- 🧠 **Smart Rate Limiting** — Low/Medium/High traffic tiers with automatic wait calculation
- 📊 **Per-Channel Tracking** — Separate limits for API, login, upload, download, search, signup
- 🎯 **Per-IP Tracking** — Track each client separately
- 🔧 **Fully Customizable** — Custom channels, custom sleep callback, auto-tracking
- 🪶 **Zero Dependencies** — Core module uses only Python stdlib
- 📦 **Optional Dependencies** — Install only what you need

## 📦 Installation

```bash
pip install waitmanager-web               # Core only
pip install waitmanager-web[flask]        # + Flask
pip install waitmanager-web[fastapi]      # + FastAPI
pip install waitmanager-web[django]       # + Django
pip install waitmanager-web[all]          # Everything
```

## 🚀 Quick Start

### Flask

```python
from flask import Flask
from waitmanager.flask import FlaskWaitManager

app = Flask(__name__)
wm = FlaskWaitManager(low_traffic=100, high_wait=2.0, auto_track=True)
wm.init_app(app)

@app.route("/api/data")
@wm.limit(channel="api")
def get_data():
    return {"status": "ok"}

@app.route("/login", methods=["POST"])
@wm.limit(channel="login", max_requests=5, window=300)
def login():
    return {"status": "ok"}
```

### FastAPI

```python
from fastapi import FastAPI, Depends
from waitmanager import WaitManager
from waitmanager.fastapi import RateLimiter

app = FastAPI()
wm = WaitManager(low_traffic=100, high_wait=2.0)
limiter = RateLimiter(wm)

@app.get("/api/data")
async def get_data(_=Depends(limiter.limit("api"))):
    return {"status": "ok"}

@app.post("/login")
async def login(_=Depends(limiter.limit("login", max_requests=5, window=300))):
    return {"status": "ok"}
```

### Django

```python
# settings.py
MIDDLEWARE = [
    "waitmanager.django.WaitManagerMiddleware",
    ...
]

WAITMANAGER_CONFIG = {
    "low_traffic": 100,
    "high_wait": 2.0,
    "auto_track": True,
}
```

```python
# views.py
from waitmanager.django import limit

@limit(channel="api")
def api_view(request):
    return JsonResponse({"status": "ok"})

@limit(channel="login", max_requests=5, window=300, block=True)
def login_view(request):
    return JsonResponse({"status": "ok"})
```

## ⚙️ Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `low_traffic` | int | 100 | Max requests for "low traffic" |
| `medium_traffic` | int | 200 | Max requests for "medium traffic" |
| `low_wait` | float | 0.0 | Delay for low traffic (seconds) |
| `medium_wait` | float | 0.5 | Delay for medium traffic |
| `high_wait` | float | 2.0 | Delay for high traffic |
| `time_window` | float | 60.0 | Time window (seconds) |
| `auto_track` | bool | False | Auto-track every request |
| `per_ip` | bool | True | Track per IP address |
| `sleep_callback` | callable | None | Custom wait time function |
| `channels` | list | None | Custom channel names |

## 🎯 Custom Sleep Callback

```python
def my_logic(channel, messages_count, last_time, **kwargs):
    if channel == "login" and messages_count > 3:
        return 30.0  # 30 second penalty
    return None  # Use default logic

wm = WaitManager(sleep_callback=my_logic)
```

## 🧪 Custom Channels

```python
wm = WaitManager(channels=["api", "login", "payment", "export"])
```

## 📄 License

MIT © [OandONE](https://github.com/OandONE)

## 🙏 Acknowledgments

Inspired by Fast Rub's [WaitManager](https://github.com/OandONE/fast_rub) — the smartest rate limiter for Rubika bots.

---

> "Good software is built on pain. WaitManager was built on Rubika's API." — OandONE
