"""Centralised, live env getters (read at call time so tests can flip them)."""
import os


def source_backend() -> str:
    return os.getenv("SOURCE_BACKEND", "sim")


def ai_summary_mode() -> str:
    return os.getenv("AI_SUMMARY", "rule")


def mqtt_url() -> str:
    return os.getenv("MQTT_URL", "mqtt://127.0.0.1:1883")


def mqtt_topic() -> str:
    return os.getenv("MQTT_TOPIC", "dashboard/snapshot")


def llm_endpoint() -> str:
    return os.getenv("HTTP_LLM_ENDPOINT", "https://api.openai.com/v1/chat/completions")


def llm_api_key() -> str:
    return os.getenv("HTTP_LLM_API_KEY", "")


def model_name() -> str:
    return os.getenv("MODEL_NAME", "gpt-4o-mini")
