import os
import yaml
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# -------------------------
# Load .env
# -------------------------
loaded = load_dotenv()
print("Dotenv loaded:", loaded)
print("APP_DEBUG:", os.getenv("APP_DEBUG"))

app = FastAPI()

# -------------------------
# CORS
# -------------------------
ALLOWED_ORIGIN = "https://dash-wl1d4h.example.com"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Defaults
# -------------------------
config = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}


def to_bool(value):
    return str(value).strip().lower() in (
        "true",
        "1",
        "yes",
        "on",
    )


def convert(key, value):
    if key in ["port", "workers"]:
        return int(value)
    elif key == "debug":
        return to_bool(value)
    else:
        return str(value)


@app.get("/effective-config")
def effective_config(set: list[str] = Query(default=[])):
    # Start with defaults
    final = config.copy()

    # -------------------------
    # YAML layer
    # -------------------------
    if os.path.exists("config.development.yaml"):
        with open("config.development.yaml", "r") as f:
            yaml_config = yaml.safe_load(f)

        if yaml_config:
            for k, v in yaml_config.items():
                final[k] = convert(k, v)

    # -------------------------
    # .env layer
    # -------------------------
    if os.getenv("APP_DEBUG") is not None:
        final["debug"] = convert("debug", os.getenv("APP_DEBUG"))

    if os.getenv("NUM_WORKERS") is not None:
        final["workers"] = convert("workers", os.getenv("NUM_WORKERS"))

    if os.getenv("APP_API_KEY") is not None:
        final["api_key"] = os.getenv("APP_API_KEY")

    # -------------------------
    # OS Environment layer
    # -------------------------
    mapping = {
        "APP_PORT": "port",
        "APP_WORKERS": "workers",
        "APP_DEBUG": "debug",
        "APP_LOG_LEVEL": "log_level",
        "APP_API_KEY": "api_key",
    }

    for env_key, cfg_key in mapping.items():
        value = os.environ.get(env_key)
        if value is not None:
            final[cfg_key] = convert(cfg_key, value)

    # -------------------------
    # CLI Overrides
    # -------------------------
    for item in set:
        if "=" in item:
            key, value = item.split("=", 1)
            final[key] = convert(key, value)

    # -------------------------
    # Mask secret
    # -------------------------
    final["api_key"] = "****"

    return final