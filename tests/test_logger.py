import unittest

from server.logger import ServerLogger, create_logger
from unittest.mock import Mock, patch
import tempfile
import shutil
import time
import os
import logging
import sys

# Mock py4godot imports before importing server modules
sys.modules['py4godot'] = Mock()
sys.modules['py4godot.classes'] = Mock()

# Add the server directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestServerLogger(unittest.TestCase):
    """Test cases for ServerLogger class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_log_dir = tempfile.mkdtemp()
        self.logger = ServerLogger('TestServer', self.test_log_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        # Close any file handlers to release locks
        for handler in self.logger.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                self.logger.logger.removeHandler(handler)

        # Wait a bit for Windows to release file handles
        time.sleep(0.1)

        # Clean up temporary directory with retry logic for Windows
        max_retries = 3
        for i in range(max_retries):
            try:
                if os.path.exists(self.test_log_dir):
                    shutil.rmtree(self.test_log_dir)
                break
            except PermissionError:
                if i < max_retries - 1:
                    time.sleep(0.5)  # Wait longer before retry
                else:
                    # If all retries fail, just leave the directory
                    pass

    def test_logger_initialization(self):
        """Test logger is properly initialized."""
        self.assertIsInstance(self.logger.logger, logging.Logger)
        self.assertEqual(self.logger.logger.name, 'TestServer')

    def test_log_directory_creation(self):
        """Test log directory is created."""
        new_log_dir = tempfile.mkdtemp()
        try:
            shutil.rmtree(new_log_dir)  # Remove it first
            # Create logger which should recreate the directory
            test_logger = ServerLogger('DirTest', new_log_dir)
            self.assertTrue(os.path.exists(new_log_dir))

            # Clean up additional logger
            for handler in test_logger.logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    test_logger.logger.removeHandler(handler)
        finally:
            # Clean up
            if os.path.exists(new_log_dir):
                try:
                    shutil.rmtree(new_log_dir)
                except PermissionError:
                    pass

    def test_log_file_creation(self):
        """Test log file is created with correct naming pattern."""
        # Create another logger to generate a new log file
        test_logger = ServerLogger('FileCreationTest', self.test_log_dir)
        test_logger.info("Test log file creation")

        log_files = [
            f for f in os.listdir(self.test_log_dir)
            if f.startswith('server_') and f.endswith('.log')
        ]
        # Should have at least one log file
        self.assertGreaterEqual(len(log_files), 1)

        # Verify file naming pattern
        for log_file in log_files:
            self.assertTrue(log_file.startswith('server_'))
            self.assertTrue(log_file.endswith('.log'))

        # Clean up additional logger
        for handler in test_logger.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                test_logger.logger.removeHandler(handler)

    def test_debug_logging(self):
        """Test debug level logging."""
        with patch.object(self.logger.logger, 'debug') as mock_debug:
            self.logger.debug("Test debug message")
            mock_debug.assert_called_once_with("Test debug message")

    def test_info_logging(self):
        """Test info level logging."""
        with patch.object(self.logger.logger, 'info') as mock_info:
            self.logger.info("Test info message")
            mock_info.assert_called_once_with("Test info message")

    def test_warning_logging(self):
        """Test warning level logging."""
        with patch.object(self.logger.logger, 'warning') as mock_warning:
            self.logger.warning("Test warning message")
            mock_warning.assert_called_once_with("Test warning message")

    def test_error_logging(self):
        """Test error level logging."""
        with patch.object(self.logger.logger, 'error') as mock_error:
            self.logger.error("Test error message")
            mock_error.assert_called_once_with("Test error message")

    def test_log_exception_with_default_level(self):
        """Test exception logging with default error level."""
        test_exception = ValueError("Test exception")

        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.log_exception("Test context", test_exception)

            # Should be called twice: once for message, once for traceback
            self.assertEqual(mock_log.call_count, 2)

            # First call should be the custom message with exception
            first_call = mock_log.call_args_list[0]
            self.assertEqual(first_call[0][0], logging.ERROR)  # Level
            self.assertIn("Test context", first_call[0][1])
            self.assertIn("Test exception", first_call[0][1])

            # Second call should be the traceback
            second_call = mock_log.call_args_list[1]
            self.assertEqual(second_call[0][0], logging.ERROR)  # Level
            self.assertIn("Traceback:", second_call[0][1])

    def test_log_exception_with_custom_level(self):
        """Test exception logging with custom level."""
        test_exception = RuntimeError("Test runtime error")

        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.log_exception(
                "Runtime error occurred", test_exception, logging.WARNING
            )

            # Both calls should use WARNING level
            for call in mock_log.call_args_list:
                self.assertEqual(call[0][0], logging.WARNING)

    def test_multiple_logger_instances_no_duplicate_handlers(self):
        """Test that multiple logger instances don't create duplicate
        handlers."""
        # Create multiple loggers with same name
        logger1 = ServerLogger('DuplicateTest', self.test_log_dir)
        logger2 = ServerLogger('DuplicateTest', self.test_log_dir)

        # Both should reference the same underlying logger
        self.assertIs(logger1.logger, logger2.logger)

        # Handler count should not increase
        handler_count = len(logger1.logger.handlers)
        logger3 = ServerLogger('DuplicateTest', self.test_log_dir)
        self.assertEqual(len(logger3.logger.handlers), handler_count)

        # Clean up additional loggers
        for logger in [logger1, logger2, logger3]:
            for handler in logger.logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    logger.logger.removeHandler(handler)

    def test_logger_setup_with_exception(self):
        """Test logger setup when directory creation fails."""
        with patch('os.makedirs',
                   side_effect=PermissionError("Permission denied")):
            with patch('builtins.print') as mock_print:
                logger = ServerLogger('ErrorTest', '/invalid/path')

                # Should fall back to basic logger
                self.assertIsInstance(logger.logger, logging.Logger)
                mock_print.assert_called()


class TestCreateLogger(unittest.TestCase):
    """Test create_logger function."""

    def test_create_logger_default_params(self):
        """Test create_logger with default parameters."""
        logger = create_logger()
        self.assertIsInstance(logger, ServerLogger)
        self.assertEqual(logger.logger.name, 'TCPServer')

        # Clean up
        for handler in logger.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                logger.logger.removeHandler(handler)

    def test_create_logger_custom_params(self):
        """Test create_logger with custom parameters."""
        test_dir = tempfile.mkdtemp()
        try:
            logger = create_logger('CustomServer', test_dir)
            self.assertIsInstance(logger, ServerLogger)
            self.assertEqual(logger.logger.name, 'CustomServer')
            self.assertTrue(os.path.exists(test_dir))

            # Clean up logger handlers
            for handler in logger.logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    logger.logger.removeHandler(handler)

            time.sleep(0.1)  # Give time for handles to close
        finally:
            if os.path.exists(test_dir):
                try:
                    shutil.rmtree(test_dir)
                except PermissionError:
                    time.sleep(0.5)
                    try:
                        shutil.rmtree(test_dir)
                    except PermissionError:
                        pass

    def test_actual_logging_to_file(self):
        """Test that messages are actually written to log file."""
        test_dir = tempfile.mkdtemp()
        try:
            logger = create_logger('FileTest', test_dir)
            logger.info("Test file logging message")

            # Flush all handlers to ensure message is written
            for handler in logger.logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()

            # Find the log file
            log_files = [
                f for f in os.listdir(test_dir) if f.endswith('.log')
            ]
            self.assertEqual(len(log_files), 1)

            # Read log file and verify message
            log_file_path = os.path.join(test_dir, log_files[0])
            with open(log_file_path, 'r') as f:
                log_content = f.read()

            self.assertIn("Test file logging message", log_content)
            self.assertIn("INFO", log_content)

            # Clean up logger handlers
            for handler in logger.logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    logger.logger.removeHandler(handler)

            time.sleep(0.1)  # Give time for handles to close
        finally:
            if os.path.exists(test_dir):
                try:
                    shutil.rmtree(test_dir)
                except PermissionError:
                    time.sleep(0.5)
                    try:
                        shutil.rmtree(test_dir)
                    except PermissionError:
                        pass


if __name__ == '__main__':
    unittest.main()
