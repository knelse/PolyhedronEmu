import unittest

from server.logger import server_logger, create_logger
from unittest.mock import Mock, patch
import tempfile
import shutil
import time
import os
import logging
import sys

sys.modules['py4godot'] = Mock()
sys.modules['py4godot.classes'] = Mock()

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestServerLogger(unittest.TestCase):
    """Test cases for server_logger class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_log_dir = tempfile.mkdtemp()
        self.logger = server_logger('TestServer', self.test_log_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        for handler in self.logger.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                self.logger.logger.removeHandler(handler)

        time.sleep(0.1)

        max_retries = 3
        for i in range(max_retries):
            try:
                if os.path.exists(self.test_log_dir):
                    shutil.rmtree(self.test_log_dir)
                break
            except PermissionError:
                if i < max_retries - 1:
                    time.sleep(0.5)
                else:
                    pass

    def test_logger_initialization(self):
        """Test logger is properly initialized."""
        self.assertIsInstance(self.logger.logger, logging.Logger)
        self.assertEqual(self.logger.logger.name, 'TestServer')

    def test_log_directory_creation(self):
        """Test log directory is created."""
        new_log_dir = tempfile.mkdtemp()
        try:
            shutil.rmtree(new_log_dir)
            test_logger = server_logger('DirTest', new_log_dir)
            self.assertTrue(os.path.exists(new_log_dir))

            for handler in test_logger.logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    test_logger.logger.removeHandler(handler)
        finally:
            if os.path.exists(new_log_dir):
                try:
                    shutil.rmtree(new_log_dir)
                except PermissionError:
                    pass

    def test_log_file_creation(self):
        """Test log file is created with correct naming pattern."""
        test_logger = server_logger('FileCreationTest', self.test_log_dir)
        test_logger.info("Test log file creation")

        log_files = [
            f for f in os.listdir(self.test_log_dir)
            if f.startswith('server_') and f.endswith('.log')
        ]
        self.assertGreaterEqual(len(log_files), 1)

        for log_file in log_files:
            self.assertTrue(log_file.startswith('server_'))
            self.assertTrue(log_file.endswith('.log'))

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

            self.assertEqual(mock_log.call_count, 2)

            first_call = mock_log.call_args_list[0]
            self.assertEqual(first_call[0][0], logging.ERROR)
            self.assertIn("Test context", first_call[0][1])
            self.assertIn("Test exception", first_call[0][1])

            second_call = mock_log.call_args_list[1]
            self.assertEqual(second_call[0][0], logging.ERROR)
            self.assertIn("Traceback:", second_call[0][1])

    def test_log_exception_with_custom_level(self):
        """Test exception logging with custom level."""
        test_exception = RuntimeError("Test runtime error")

        with patch.object(self.logger.logger, 'log') as mock_log:
            self.logger.log_exception(
                "Runtime error occurred", test_exception, logging.WARNING
            )

            for call in mock_log.call_args_list:
                self.assertEqual(call[0][0], logging.WARNING)

    def test_multiple_logger_instances_no_duplicate_handlers(self):
        """Test that multiple logger instances don't create duplicate
        handlers."""
        logger1 = server_logger('DuplicateTest', self.test_log_dir)
        logger2 = server_logger('DuplicateTest', self.test_log_dir)

        self.assertIs(logger1.logger, logger2.logger)

        handler_count = len(logger1.logger.handlers)
        logger3 = server_logger('DuplicateTest', self.test_log_dir)
        self.assertEqual(len(logger3.logger.handlers), handler_count)

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
                logger = server_logger('ErrorTest', '/invalid/path')

                self.assertIsInstance(logger.logger, logging.Logger)
                mock_print.assert_called()


class TestCreateLogger(unittest.TestCase):
    """Test create_logger function."""

    def test_create_logger_default_params(self):
        """Test create_logger with default parameters."""
        logger = create_logger()
        self.assertIsInstance(logger, server_logger)
        self.assertEqual(logger.logger.name, 'TCPServer')

        for handler in logger.logger.handlers[:]:
            if isinstance(handler, logging.FileHandler):
                handler.close()
                logger.logger.removeHandler(handler)

    def test_create_logger_custom_params(self):
        """Test create_logger with custom parameters."""
        test_dir = tempfile.mkdtemp()
        try:
            logger = create_logger('CustomServer', test_dir)
            self.assertIsInstance(logger, server_logger)
            self.assertEqual(logger.logger.name, 'CustomServer')
            self.assertTrue(os.path.exists(test_dir))

            for handler in logger.logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    logger.logger.removeHandler(handler)

            time.sleep(0.1)
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

            for handler in logger.logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()

            log_files = [
                f for f in os.listdir(test_dir) if f.endswith('.log')
            ]
            self.assertEqual(len(log_files), 1)

            log_file_path = os.path.join(test_dir, log_files[0])
            with open(log_file_path, 'r') as f:
                log_content = f.read()

            self.assertIn("Test file logging message", log_content)
            self.assertIn("INFO", log_content)

            for handler in logger.logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    logger.logger.removeHandler(handler)

            time.sleep(0.1)
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
