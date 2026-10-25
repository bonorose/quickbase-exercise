#!/usr/bin/env python3
# ******************************************************************************
# * @file    logging.py
# * @author  Simeon Marlokov
# * @brief   Loguru setup
# * @date    25.10.2026
# ******************************************************************************
import sys

from loguru import logger


def setup_logging(level: str) -> None:
    logger.remove()
    logger.add(sys.stdout, level=level.upper(), enqueue=True, backtrace=False)
