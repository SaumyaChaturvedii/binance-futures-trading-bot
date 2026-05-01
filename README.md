# Binance Futures Testnet Trading Bot

Simple Python bot for placing orders on the Binance Futures Testnet (USDT-M). Built as a CLI tool with support for Market, Limit, and Stop-Limit orders.

## Project Structure

```
trading_bot/
  bot/
    __init__.py
    client.py          # binance API wrapper (signing, http)
    orders.py          # order logic + formatting
    validators.py      # input validation
    logging_config.py  # logging setup
  cli.py               # CLI entry point
  .env.example
  requirements.txt
  README.md
```

## Setup

### Prerequisites
- Python 3.8+
- Binance Futures Testnet account ([sign up here](https://testnet.binancefuture.com/))

### Install

```bash
git clone https://github.com/your-username/trading_bot.git
cd trading_bot

# create venv (optional but recommended)
python -m venv venv
venv\Scripts\activate   # windows
# source venv/bin/activate  # mac/linux

pip install -r requirements.txt
```

### Configure API Keys

1. Get your API key and secret from the [testnet](https://testnet.binancefuture.com/)
2. Copy the example env file and fill in your keys:

```bash
cp .env.example .env
```

Edit `.env`:
```
BINANCE_API_KEY=your_key_here
BINANCE_API_SECRET=your_secret_here
```

> **Don't commit your .env file!** It's in .gitignore already.

## Usage

### CLI Mode

```bash
# market buy
python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001

# limit sell
python cli.py order -s ETHUSDT --side SELL -t LIMIT -q 0.01 -p 3500

# stop-limit
python cli.py order -s BTCUSDT --side SELL -t STOP_LIMIT -q 0.001 -p 90000 --stop-price 91000

# help
python cli.py --help
python cli.py order --help
```

### Interactive Mode

```bash
python cli.py interactive
```

This gives you a menu where you can place orders, check account info, and look up prices without remembering all the flags.

## CLI Arguments

| Flag | Short | Description |
|------|-------|-------------|
| `--symbol` | `-s` | Trading pair, e.g. BTCUSDT |
| `--side` | | BUY or SELL |
| `--type` | `-t` | MARKET, LIMIT, or STOP_LIMIT |
| `--quantity` | `-q` | Order quantity |
| `--price` | `-p` | Limit price (required for LIMIT/STOP_LIMIT) |
| `--stop-price` | | Stop trigger price (for STOP_LIMIT) |
| `--time-in-force` | | GTC (default), IOC, or FOK |

## Logging

Logs go to `logs/` with a timestamp in the filename. The console shows INFO level, the log file captures everything (DEBUG).

Check the `logs/` folder for sample log output from test orders.

## Architecture

The code is split into layers:
- **CLI** (`cli.py`) - handles argument parsing and user interaction
- **Validators** (`validators.py`) - validates all inputs before they hit the API
- **Orders** (`orders.py`) - formats params, calls the client, shows results
- **Client** (`client.py`) - low-level HTTP + signing, talks to Binance

This keeps things testable and makes it easy to swap out the CLI for a web interface later if needed.

## Assumptions

- This is testnet only - don't point it at the real Binance API
- All orders are USDT-M futures
- You're responsible for using valid quantities/prices for each symbol (the API will reject bad values with a clear error)
- LIMIT and STOP_LIMIT default to GTC if you don't specify time-in-force
- The bot places individual orders, it doesn't manage positions or run strategies

## Bonus Features

- **Stop-Limit orders** - full support via `--type STOP_LIMIT`
- **Interactive mode** - guided menu with account info and price lookups
