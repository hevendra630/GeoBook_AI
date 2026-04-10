from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Chatbot"

    environment: str = "dev"

    log_level: str = "INFO"

    backend_cors_origins: str = "http://localhost:5173,http://localhost:5174"

    jwt_secret_key: str

    jwt_algorithm: str = "HS256"

    jwt_access_token_expire_minutes: int = 60

    database_url: str

    

    google_maps_api_key: str | None = None

    gemini_api_key: str | None = None

    

    

    osm_user_agent: str = "AI-CHATBOT/1.0 (contact: admin@example.com)"

    osm_nominatim_base_url: str = "https://nominatim.openstreetmap.org"

    osm_nominatim_email: str | None = None

    

    osm_photon_base_url: str = "https://photon.komoot.io"

    

    osm_overpass_url: str = "https://overpass-api.de/api/interpreter,https://overpass.kumi.systems/api/interpreter,https://overpass.nchc.org.tw/api/interpreter"

    rate_limit_default: str = "60/minute"

    

    smtp_host: str | None = None

    smtp_port: int = 587

    smtp_username: str | None = None

    smtp_password: str | None = None

    smtp_from_email: str | None = None

    def cors_origins(self) -> list[str]:

        

        raw = [o.strip() for o in self.backend_cors_origins.split(",")]

        return [o for o in raw if o]

settings = Settings()  

