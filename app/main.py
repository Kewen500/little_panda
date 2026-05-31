from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.config import APP_NAME, get_refresh_interval_seconds, load_provider_config
from app.providers.factory import build_provider
from app.window import FloatingUsageWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    icon_path = Path(__file__).resolve().parents[1] / "assets" / "api-balance-widget.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    provider_config = load_provider_config()

    window = FloatingUsageWindow(
        provider=build_provider(provider_config),
        refresh_interval_seconds=get_refresh_interval_seconds(provider_config),
    )
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
