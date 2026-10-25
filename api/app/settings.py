"""Service configuration read from the environment."""

from collections.abc import Mapping
from dataclasses import dataclass

MB = 1024 * 1024


@dataclass(frozen=True)
class Settings:
    database_url: str
    web_origin: str
    port: int = 8300
    rate_limit_per_hour: int = 20
    max_upload_bytes: int = 20 * MB
    db_schema: str | None = None

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "Settings":
        errors: list[str] = []
        required = {name: env.get(name, "").strip() for name in ("DATABASE_URL", "WEB_ORIGIN")}
        errors += [f"{name} is required" for name, value in required.items() if not value]

        def positive(name: str, default: int) -> int:
            raw = env.get(name, "").strip()
            if not raw:
                return default
            if raw.isdigit() and int(raw) > 0:
                return int(raw)
            errors.append(f"{name} must be a positive integer, got {raw!r}")
            return default

        port = positive("PORT", 8300)
        per_hour = positive("RATE_LIMIT_PER_HOUR", 20)
        max_bytes = positive("MAX_UPLOAD_BYTES", 20 * MB)
        if errors:
            raise ValueError("; ".join(errors))
        return cls(
            database_url=required["DATABASE_URL"],
            web_origin=required["WEB_ORIGIN"],
            port=port,
            rate_limit_per_hour=per_hour,
            max_upload_bytes=max_bytes,
        )
