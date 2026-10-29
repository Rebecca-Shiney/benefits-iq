import json
import logging
import os


class SafeFormatter(logging.Formatter):
    def format(self, record):
        event = {"level": record.levelname, "logger": record.name}
        if record.name == "benefits":
            event["message"] = record.getMessage()
        else:
            event["event"] = "library_error" if record.levelno >= logging.ERROR else "library_status"
        if record.exc_info and record.exc_info[0]:
            event["exception_type"] = record.exc_info[0].__name__
        return json.dumps(event)


def logging_configuration():
    return {
        "version": 1, "disable_existing_loggers": False,
        "formatters": {"safe": {"()": SafeFormatter}},
        "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "safe", "stream": "ext://sys.stdout"}},
        "root": {"handlers": ["console"], "level": "WARNING"},
        "loggers": {
            "benefits": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"handlers": [], "propagate": False},
        },
    }


def main():
    if os.environ.get("BENEFITS_PROFILE") not in {"starter", "showcase"}:
        raise RuntimeError("CLOUD_ENTRYPOINT_REQUIRES_STARTER")
    if os.environ.get("OTEL_SDK_DISABLED", "").lower() != "true":
        raise RuntimeError("CLOUD_TRACING_MUST_BE_DISABLED")
    import uvicorn
    uvicorn.run("service.app:app", host="0.0.0.0", port=8000, access_log=False,
                log_config=logging_configuration())


if __name__ == "__main__":
    main()
