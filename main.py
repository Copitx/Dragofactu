#!/usr/bin/env python3
"""Compatibility entry point.

This wrapper keeps historical `python3 main.py` usage working,
delegating startup to the launcher that manages virtualenv and dependencies.
"""

from launch_dragofactu_fixed import main


if __name__ == "__main__":
	main()
