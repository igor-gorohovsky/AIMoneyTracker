# Expenses Tracker

A Telegram bot for tracking personal expenses with multi-currency support.

## Features

- Telegram bot interface
- PostgreSQL database
- Multi-currency support with automatic exchange rate updates
- Docker-based deployment

## Setup

1. Clone the repository
2. Create a `.env` file with:
   ```
   TG_TOKEN=your_telegram_bot_token
   POSTGRES_USER=postgres
   POSTGRES_DB=expenses
   POSTGRES_PASSWORD=password
   DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/expenses
   CURRENCY_API_KEY=your_exchangerate_api_key
   ```
3. Run with Docker Compose:
   ```
   docker compose up -d
   ```

## Services

The application consists of two main services:

1. **Bot Service**: Handles Telegram user interactions
2. **Worker Service**: Runs scheduled tasks including currency rate updates

## Currency Exchange Rates

The worker service automatically fetches and updates exchange rates daily. It uses the [ExchangeRate-API](https://www.exchangerate-api.com/) to get the latest rates.

To use this feature:
1. Sign up at [ExchangeRate-API](https://www.exchangerate-api.com/) to get an API key
2. Add your API key to the `.env` file as `CURRENCY_API_KEY`

## Development

1. Install Poetry
2. Run `poetry install`
3. Run the tests with `poetry run pytest`
