#!/usr/bin/env python3
# ******************************************************************************
# * @file    __main__.py
# * @author  Simeon Marlokov
# * @brief   python -m src.seed [--reset]
# * @date    25.10.2026
# ******************************************************************************
import argparse
import asyncio

from src.seed.run import seed


def main() -> None:
    parser = argparse.ArgumentParser(description="Idempotent development seed. Refuses APP_ENV=production.")
    parser.add_argument("--reset", action="store_true", help="Truncate organization data, then seed")
    args = parser.parse_args()
    asyncio.run(seed(reset=args.reset))


if __name__ == "__main__":
    main()
