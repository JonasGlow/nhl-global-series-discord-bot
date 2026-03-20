from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Discord
    discord_token: str
    discord_channel_id: int
    discord_user_id: int

    # Ticketmaster
    ticketmaster_api_key: str

    # Scheduler - when the bot checks for updates (Timezone: Europe/Berlin)
    check_hour: int = 12

    # Search words for Ticketmaster
    tm_keyword: str = "NHL"
    tm_city: str = "Düsseldorf"
    tm_country_code: str = "DE"


settings = Settings()
