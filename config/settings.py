from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # AI
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    ai_model: str = Field(default="claude-sonnet-4-20250514", alias="AI_MODEL")

    # Jira Cloud
    jira_base_url: str = Field(default="", alias="JIRA_BASE_URL")
    jira_email: str = Field(default="", alias="JIRA_EMAIL")
    jira_api_token: str = Field(default="", alias="JIRA_API_TOKEN")
    jira_project_key: str = Field(default="QA", alias="JIRA_PROJECT_KEY")

    # GitHub
    github_token: str = Field(default="", alias="GITHUB_TOKEN")
    github_repo: str = Field(default="", alias="GITHUB_REPO")
    github_default_branch: str = Field(default="main", alias="GITHUB_DEFAULT_BRANCH")

    # App
    secret_key: str = Field(default="changeme", alias="SECRET_KEY")
    database_url: str = Field(default="sqlite:///./regression_pilot.db", alias="DATABASE_URL")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Agent behaviour
    max_fix_retries: int = 3
    confidence_threshold: float = 0.75  # Below this → human review queue
    test_timeout_seconds: int = 60


settings = Settings()
