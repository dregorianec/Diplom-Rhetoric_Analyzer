from pydantic_settings import BaseSettings
from pydantic import Field
from pathlib import Path


class Settings(BaseSettings):
    # LLM (LiteLLM / OpenAI-compatible)
    llm_api_key: str = Field(..., env="LLM_API_KEY")
    llm_api_base: str | None = Field(None, env="LLM_API_BASE")  # None = использовать litellm по умолчанию
    llm_model: str = Field("gpt-4", env="LLM_MODEL")  # Модель через LiteLLM
    llm_temperature: float = Field(0.0, env="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(256, env="LLM_MAX_TOKENS")
    llm_timeout_s: float = Field(120.0, env="LLM_TIMEOUT_S")
    llm_max_retries: int = Field(2, env="LLM_MAX_RETRIES")
    llm_sleep_between_calls_s: float = Field(0.3, env="LLM_SLEEP_BETWEEN_CALLS_S")
    llm_use_logprobs: bool = Field(False, env="LLM_USE_LOGPROBS")  # Использовать logprobs для confidence
    analysis_max_groups: int = Field(20, env="ANALYSIS_MAX_GROUPS")  # ограничение нагрузки на LLM

    # RapidAPI - YouTube Search & Download
    rapidapi_key: str | None = Field(None, env="RAPIDAPI_KEY")
    rapidapi_host: str | None = Field(None, env="RAPIDAPI_HOST")
    rapidapi_endpoint: str | None = Field(None, env="RAPIDAPI_ENDPOINT")

    # Apify (альтернатива RapidAPI)
    apify_token: str | None = Field(None, env="APIFY_TOKEN")
    apify_actor_id: str | None = Field(None, env="APIFY_ACTOR_ID")

    # Whisper (локальная модель)
    whisper_model_path: Path = Field(Path("./models/whisper"), env="WHISPER_MODEL_PATH")
    whisper_device: str = Field("cuda", env="WHISPER_DEVICE")  # cuda / cpu
    whisper_compute_type: str = Field("float16", env="WHISPER_COMPUTE_TYPE")  # float16 / int8 / float32
    whisper_language: str = Field("en", env="WHISPER_LANGUAGE")  # en / ru / auto

    # Storage directories
    data_dir: Path = Field(Path("./data"), env="DATA_DIR")
    video_subdir: str = Field("videos", env="VIDEO_SUBDIR")
    result_subdir: str = Field("results", env="RESULT_SUBDIR")
    transcript_subdir: str = Field("transcripts", env="TRANSCRIPT_SUBDIR")

    # YouTube Search settings
    youtube_max_results: int = Field(1, env="YOUTUBE_MAX_RESULTS")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore"
    }

    @property
    def videos_dir(self) -> Path:
        return self.data_dir / self.video_subdir

    @property
    def transcripts_dir(self) -> Path:
        return self.data_dir / self.transcript_subdir

    @property
    def results_dir(self) -> Path:
        return self.data_dir / self.result_subdir


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
