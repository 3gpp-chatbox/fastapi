import atexit
import json
import logging
import logging.config
from pathlib import Path

# Configure logging
logger = logging.getLogger("my_app")


def setup_logger():
    print("Setting up logger...")
    config_file = Path(__file__).parent / "logging_config.json"
    with open(config_file) as f:
        config = json.load(f)
    # Ensure log directory exists
    file_path = Path(config["handlers"]["file"]["filename"])
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(
            f"WARNING: Could not create log directory {file_path.parent}: {e}",
        )
    logging.config.dictConfig(config)
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)


if __name__ == "__main__":
    setup_logger()
    # If this module is run directly, set up the logger
    logger.debug("This is a debug message.")
    logger.info("This is an info message.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
