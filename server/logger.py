import logging
import os
import traceback
from datetime import datetime


def cleanup_old_logs(log_dir: str = "logs", max_files: int = 20) -> None:
    """
    Clean up old log files, keeping only the most recent max_files.

    Args:
        log_dir: Directory containing log files
        max_files: Maximum number of log files to keep
    """
    try:
        if not os.path.exists(log_dir):
            return

        log_files = []
        for filename in os.listdir(log_dir):
            if filename.startswith("server_") and filename.endswith(".log"):
                filepath = os.path.join(log_dir, filename)
                if os.path.isfile(filepath):
                    log_files.append((filepath, os.path.getmtime(filepath)))

        if len(log_files) <= max_files:
            return

        log_files.sort(key=lambda x: x[1], reverse=True)

        files_to_remove = log_files[max_files:]
        for filepath, _ in files_to_remove:
            try:
                os.remove(filepath)
                print(f"Removed old log file: {os.path.basename(filepath)}")
            except Exception as e:
                print(f"Failed to remove log file {filepath}: {e}")

        if files_to_remove:
            print(
                f"Log cleanup complete: kept {max_files} most recent files, "
                f"removed {len(files_to_remove)} old files"
            )

    except Exception as e:
        print(f"Error during log cleanup: {e}")


class ServerLogger:
    def __init__(self, name: str = "TCPServer", log_dir: str = "logs"):
        self.logger = self._setup_logger(name, log_dir)

    def _setup_logger(self, name: str, log_dir: str) -> logging.Logger:
        """
        Set up and configure a logger with both file and console handlers.
        Creates timestamped log files in the specified directory.
        """
        try:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)

            cleanup_old_logs(log_dir)

            logger = logging.getLogger(name)
            logger.setLevel(logging.DEBUG)

            if logger.handlers:
                return logger

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{log_dir}/server_{timestamp}.log"
            fh = logging.FileHandler(filename)
            fh.setLevel(logging.DEBUG)

            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)

            fmt = "%(asctime)s - %(levelname)s - %(message)s"
            formatter = logging.Formatter(fmt)
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)

            logger.addHandler(fh)
            logger.addHandler(ch)

            logger.info("Logging system initialized")
            return logger

        except Exception as e:
            print(f"Error setting up logging: {str(e)}")
            basic_logger = logging.getLogger(name)
            basic_logger.setLevel(logging.DEBUG)
            if not basic_logger.handlers:
                basic_logger.addHandler(logging.StreamHandler())
            return basic_logger

    def log_exception(
        self, message: str, exc: Exception, level: int = logging.ERROR
    ) -> None:
        """
        Log an exception with a custom message and full traceback.

        Args:
            message: Custom message describing the context of the exception
            exc: The exception object
            level: Logging level (default: logging.ERROR)
        """
        self.logger.log(level, f"{message}: {str(exc)}")
        self.logger.log(level, "Traceback:\n" + traceback.format_exc())

    def debug(self, msg: str) -> None:
        self.logger.debug(msg)

    def info(self, msg: str) -> None:
        self.logger.info(msg)

    def warning(self, msg: str) -> None:
        self.logger.warning(msg)

    def error(self, msg: str) -> None:
        self.logger.error(msg)


def create_logger(name: str = "TCPServer", log_dir: str = "logs") -> ServerLogger:
    """Create and return a new ServerLogger instance."""
    return ServerLogger(name, log_dir)
