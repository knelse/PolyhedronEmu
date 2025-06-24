"""
Signal handler module for graceful server shutdown.
Handles SIGINT (Ctrl+C) and SIGTERM signals to ensure clean thread termination.
"""

import signal
import sys
import threading
import time
from typing import Callable


class SignalHandler:
    """
    Handles system signals for graceful server shutdown.
    Ensures all threads are properly terminated when receiving interrupt signals.
    """

    def __init__(self, logger=None):
        """
        Initialize the signal handler.

        Args:
            logger: Optional logger instance for logging shutdown events
        """
        self.logger = logger
        self.shutdown_callbacks = []
        self.shutdown_initiated = False
        self._original_sigint = None
        self._original_sigterm = None

    def add_shutdown_callback(self, callback: Callable[[], None]) -> None:
        """
        Add a callback function to be called during shutdown.

        Args:
            callback: Function to call during shutdown
        """
        self.shutdown_callbacks.append(callback)

    def setup_signal_handlers(self) -> None:
        """
        Set up signal handlers for SIGINT (Ctrl+C) and SIGTERM.
        """
        # Store original handlers
        self._original_sigint = signal.signal(signal.SIGINT, self._signal_handler)
        self._original_sigterm = signal.signal(signal.SIGTERM, self._signal_handler)

        if self.logger:
            self.logger.info("Signal handlers installed for SIGINT and SIGTERM")

    def _signal_handler(self, signum: int, frame) -> None:
        """
        Handle received signals by initiating graceful shutdown.

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        if self.shutdown_initiated:
            # If shutdown is already in progress, force exit
            if self.logger:
                self.logger.warning(f"Force exit requested (signal {signum})")
            sys.exit(1)

        self.shutdown_initiated = True
        signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"

        if self.logger:
            self.logger.info(f"Received {signal_name}, initiating graceful shutdown...")
        else:
            print(f"Received {signal_name}, initiating graceful shutdown...")

        # Run shutdown callbacks in a separate thread to avoid blocking
        shutdown_thread = threading.Thread(
            target=self._execute_shutdown, name="SignalShutdownThread"
        )
        shutdown_thread.daemon = True
        shutdown_thread.start()

        # Give shutdown thread some time to complete
        shutdown_thread.join(timeout=10.0)

        if shutdown_thread.is_alive():
            if self.logger:
                self.logger.warning("Shutdown timeout reached, forcing exit")
            else:
                print("Shutdown timeout reached, forcing exit")

        sys.exit(0)

    def _execute_shutdown(self) -> None:
        """
        Execute all shutdown callbacks and clean up resources.
        """
        start_time = time.time()

        for i, callback in enumerate(self.shutdown_callbacks):
            try:
                if self.logger:
                    self.logger.debug(
                        f"Executing shutdown callback {i + 1}/{len(self.shutdown_callbacks)}"
                    )
                callback()
            except Exception as e:
                if self.logger:
                    self.logger.log_exception(f"Error in shutdown callback {i + 1}", e)
                else:
                    print(f"Error in shutdown callback {i + 1}: {e}")

        elapsed = time.time() - start_time
        if self.logger:
            self.logger.info(f"Graceful shutdown completed in {elapsed:.2f} seconds")
        else:
            print(f"Graceful shutdown completed in {elapsed:.2f} seconds")

    def restore_signal_handlers(self) -> None:
        """
        Restore original signal handlers.
        """
        if self._original_sigint is not None:
            signal.signal(signal.SIGINT, self._original_sigint)
        if self._original_sigterm is not None:
            signal.signal(signal.SIGTERM, self._original_sigterm)

        if self.logger:
            self.logger.debug("Original signal handlers restored")

    def force_thread_cleanup(self, timeout: float = 5.0) -> None:
        """
        Force cleanup of all non-daemon threads.

        Args:
            timeout: Maximum time to wait for threads to finish
        """
        main_thread = threading.main_thread()
        active_threads = [
            t for t in threading.enumerate() if t != main_thread and t.is_alive()
        ]

        if not active_threads:
            if self.logger:
                self.logger.debug("No active threads to clean up")
            return

        if self.logger:
            self.logger.info(f"Cleaning up {len(active_threads)} active threads...")
        else:
            print(f"Cleaning up {len(active_threads)} active threads...")

        # Log thread information
        for thread in active_threads:
            thread_info = (
                f"Thread: {thread.name}, Daemon: {thread.daemon}, "
                f"Alive: {thread.is_alive()}"
            )
            if self.logger:
                self.logger.debug(thread_info)
            else:
                print(thread_info)

        # Wait for threads to finish with timeout
        start_time = time.time()
        for thread in active_threads:
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time <= 0:
                break

            try:
                thread.join(timeout=remaining_time)
                if thread.is_alive():
                    if self.logger:
                        self.logger.warning(
                            f"Thread {thread.name} did not terminate within timeout"
                        )
                    else:
                        print(f"Thread {thread.name} did not terminate within timeout")
            except Exception as e:
                if self.logger:
                    self.logger.log_exception(f"Error joining thread {thread.name}", e)
                else:
                    print(f"Error joining thread {thread.name}: {e}")

        # Check for remaining threads
        remaining_threads = [
            t for t in threading.enumerate() if t != main_thread and t.is_alive()
        ]
        if remaining_threads:
            if self.logger:
                self.logger.warning(
                    f"{len(remaining_threads)} threads still active after cleanup"
                )
            else:
                print(f"{len(remaining_threads)} threads still active after cleanup")
        else:
            if self.logger:
                self.logger.info("All threads successfully cleaned up")
            else:
                print("All threads successfully cleaned up")
