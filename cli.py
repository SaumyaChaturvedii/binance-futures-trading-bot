"""
CLI entry point for the trading bot.

Supports two modes:
  - Direct: python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
  - Interactive: python cli.py interactive
"""

import sys
import io

# windows console doesn't handle utf-8 well by default
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

import argparse
import os
import logging

from dotenv import load_dotenv

from bot.logging_config import setup_logging
from bot.client import BinanceClient, BinanceAPIError
from bot.validators import validate_all, ValidationError
from bot.orders import place_order

logger = logging.getLogger("trading_bot")


def get_credentials():
    """Load API keys from .env or environment variables."""
    load_dotenv()

    key = os.getenv("BINANCE_API_KEY", "").strip()
    secret = os.getenv("BINANCE_API_SECRET", "").strip()

    if not key or not secret:
        print("\n  ERROR: API credentials not found!")
        print("  Set BINANCE_API_KEY and BINANCE_API_SECRET in a .env file")
        print("  or as environment variables.\n")
        print("  Example .env:")
        print("    BINANCE_API_KEY=your_key_here")
        print("    BINANCE_API_SECRET=your_secret_here\n")
        sys.exit(1)

    logger.info("API credentials loaded")
    return key, secret


def cmd_order(args):
    """Handle the 'order' subcommand."""
    # validate first
    try:
        params = validate_all(
            symbol=args.symbol,
            side=args.side,
            order_type=args.type,
            quantity=str(args.quantity),
            price=str(args.price) if args.price is not None else None,
            stop_price=str(args.stop_price) if args.stop_price is not None else None,
            time_in_force=args.time_in_force,
        )
    except ValidationError as e:
        print(f"\n  Validation error: {e}\n")
        logger.error("Validation failed: %s", e)
        sys.exit(1)

    key, secret = get_credentials()
    client = BinanceClient(key, secret)

    try:
        place_order(
            client=client,
            symbol=params["symbol"],
            side=params["side"],
            order_type=params["order_type"],
            quantity=params["quantity"],
            price=params["price"],
            stop_price=params["stop_price"],
            time_in_force=params["time_in_force"],
        )
    except BinanceAPIError as e:
        print(f"\n  API Error: {e}\n")
        logger.error("Order failed: %s", e)
        sys.exit(1)
    except Exception as e:
        print(f"\n  Something went wrong: {e}\n")
        logger.exception("Unexpected error placing order")
        sys.exit(1)


def cmd_interactive(args):
    """Interactive menu for placing orders."""
    key, secret = get_credentials()
    client = BinanceClient(key, secret)

    print("\n" + "=" * 50)
    print("  Binance Futures Testnet - Trading Bot")
    print("  " + "-" * 40)
    print("  Interactive Mode")
    print("=" * 50)

    while True:
        print("\n  +----------------------------------+")
        print("  |  1. Place MARKET Order            |")
        print("  |  2. Place LIMIT Order             |")
        print("  |  3. Place STOP-LIMIT Order        |")
        print("  |  4. Account Info                  |")
        print("  |  5. Ticker Price                  |")
        print("  |  0. Exit                          |")
        print("  +----------------------------------+")

        choice = input("\n  Choice [0-5]: ").strip()

        if choice == "0":
            print("\n  Bye!\n")
            break
        elif choice == "1":
            _do_order(client, "MARKET")
        elif choice == "2":
            _do_order(client, "LIMIT")
        elif choice == "3":
            _do_order(client, "STOP_LIMIT")
        elif choice == "4":
            _show_account(client)
        elif choice == "5":
            _show_ticker(client)
        else:
            print("  Invalid choice, try again.")


def _do_order(client, order_type):
    """Collect inputs and place an order interactively."""
    print(f"\n  --- {order_type} Order ---\n")
    try:
        symbol = input("  Symbol (e.g. BTCUSDT): ").strip()
        side = input("  Side (BUY/SELL): ").strip()
        quantity = input("  Quantity: ").strip()

        price = None
        stop_price = None
        tif = None

        if order_type in ("LIMIT", "STOP_LIMIT"):
            price = input("  Price: ").strip()
            tif_in = input("  Time-in-force [GTC/IOC/FOK] (enter for GTC): ").strip()
            tif = tif_in if tif_in else None

        if order_type == "STOP_LIMIT":
            stop_price = input("  Stop price: ").strip()

        params = validate_all(
            symbol=symbol, side=side, order_type=order_type,
            quantity=quantity,
            price=price or None,
            stop_price=stop_price or None,
            time_in_force=tif,
        )

        place_order(
            client, params["symbol"], params["side"], params["order_type"],
            params["quantity"], params["price"], params["stop_price"],
            params["time_in_force"],
        )
    except ValidationError as e:
        print(f"\n  Validation error: {e}\n")
        logger.error("Validation error: %s", e)
    except BinanceAPIError as e:
        print(f"\n  API error: {e}\n")
        logger.error("API error: %s", e)
    except KeyboardInterrupt:
        print("\n  Cancelled.\n")
    except Exception as e:
        print(f"\n  Error: {e}\n")
        logger.exception("Unexpected error in interactive order")


def _show_account(client):
    """Show basic account info."""
    try:
        print("\n  Fetching account...")
        acct = client.get_account()

        print("\n  " + "=" * 45)
        print("  Account Info")
        print("  " + "=" * 45)
        print(f"  Wallet Balance  : {acct.get('totalWalletBalance', '?')} USDT")
        print(f"  Available       : {acct.get('availableBalance', '?')} USDT")
        print(f"  Unrealized PnL  : {acct.get('totalUnrealizedProfit', '?')} USDT")

        # show any open positions
        positions = [p for p in acct.get("positions", [])
                     if float(p.get("positionAmt", 0)) != 0]
        if positions:
            print("\n  Open positions:")
            for p in positions:
                print(f"    {p['symbol']}: {p['positionAmt']} "
                      f"(entry: {p.get('entryPrice', '?')}, "
                      f"pnl: {p.get('unrealizedProfit', '?')})")
        else:
            print("  No open positions.")
        print("  " + "=" * 45)

    except BinanceAPIError as e:
        print(f"\n  API error: {e}\n")
    except Exception as e:
        print(f"\n  Error: {e}\n")


def _show_ticker(client):
    """Quick price check."""
    try:
        symbol = input("\n  Symbol: ").strip().upper()
        data = client.get_ticker_price(symbol)
        print(f"\n  {data['symbol']}: ${data['price']}\n")
    except BinanceAPIError as e:
        print(f"\n  API error: {e}\n")
    except Exception as e:
        print(f"\n  Error: {e}\n")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        description="Binance Futures Testnet Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py order --symbol BTCUSDT --side BUY --type MARKET --quantity 0.001
  python cli.py order -s ETHUSDT --side SELL -t LIMIT -q 0.01 -p 3500
  python cli.py order -s BTCUSDT --side SELL -t STOP_LIMIT -q 0.001 -p 90000 --stop-price 91000
  python cli.py interactive
        """,
    )

    subs = parser.add_subparsers(dest="command", help="Commands")

    # order subcommand
    op = subs.add_parser("order", help="Place an order")
    op.add_argument("--symbol", "-s", required=True, help="Trading pair (e.g. BTCUSDT)")
    op.add_argument("--side", required=True, choices=["BUY", "SELL", "buy", "sell"])
    op.add_argument("--type", "-t", required=True,
                    choices=["MARKET", "LIMIT", "STOP_LIMIT", "market", "limit", "stop_limit"],
                    help="Order type")
    op.add_argument("--quantity", "-q", required=True, type=float, help="Amount")
    op.add_argument("--price", "-p", type=float, default=None,
                    help="Limit price (required for LIMIT/STOP_LIMIT)")
    op.add_argument("--stop-price", type=float, default=None,
                    help="Stop trigger price (for STOP_LIMIT)")
    op.add_argument("--time-in-force", choices=["GTC", "IOC", "FOK"], default=None)
    op.set_defaults(func=cmd_order)

    # interactive mode
    ip = subs.add_parser("interactive", help="Interactive trading menu")
    ip.set_defaults(func=cmd_interactive)

    return parser


def main():
    setup_logging()

    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
