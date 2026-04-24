"""SimpleDictation for Windows -- entry point."""

import logging
import sys

# Configure logging before anything else
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("simpledictation.log", encoding="utf-8"),
    ],
)

from app import SimpleDictationApp


def main():
    app = SimpleDictationApp()
    try:
        app.run()
    except KeyboardInterrupt:
        app.quit()


if __name__ == "__main__":
    main()
