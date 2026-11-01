from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """应用配置，支持通过环境变量覆盖。"""

    app_name: str = "人寿海外智能知识库"
    app_version: str = "1.0.0"
    database_url: str = "sqlite:///./data/kb.db"
    upload_dir: str = "./data/uploads"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    llm_mode: str = "auto"
    llm_timeout: int = 30

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        if not path.is_absolute():
            path = BASE_DIR / path
        path.mkdir(parents=True, exist_ok=True)
        return path

    def sqlalchemy_url(self) -> str:
        """把相对 SQLite 路径解析到 fastapi 目录下，便于任意工作目录启动。"""
        url = self.database_url
        if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
            raw = url[len("sqlite:///"):]
            if not raw.startswith(":memory:"):
                path = Path(raw)
                if not path.is_absolute():
                    path = BASE_DIR / path
                path.parent.mkdir(parents=True, exist_ok=True)
                return f"sqlite:///{path.as_posix()}"
        return url


settings = Settings()
