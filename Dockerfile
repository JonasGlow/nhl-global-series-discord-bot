FROM debian:bookworm-slim
 
# Install ca-certificates
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*
 
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
 
WORKDIR /nhl-global-series-discord-bot
 
COPY . .
 
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
 
# Install dependencies
RUN uv sync --frozen
 
CMD ["uv", "run", "python", "-m", "nhl_global_series_discord_bot.main"]