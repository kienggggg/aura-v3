"""Launch only AURA Chat v1; no legacy dashboard or daemon."""

from interface.chat_app import main


if __name__ == "__main__":
    raise SystemExit(main())
