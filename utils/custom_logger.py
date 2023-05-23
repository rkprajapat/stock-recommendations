# # Copyright (C) KonaAI - All Rights Reserved

"""This module provides the logging capability
"""

import datetime
import inspect
import logging
import logging.handlers
import os
import sys

import coloredlogs
import humanize

# Custom Console Logger #
DEFAULT_LOG_LEVEL = logging.DEBUG
DEFAULT_LOG_NAME = "app_Log"
# DEFAULT FIELD STYLES
STREAM_DEFAULT_FIELD_STYLES = {
    "lineno": {"color": 127},
    "name": {"color": "black"},
    "levelname": {"color": 180, "bold": True},
    "funcName": {"color": "black"},
    "asctime": {"color": "black", "bold": True},
    "message": {"color": "white"},
    "filename": {"color": "black"},
    "module": {"color": "black"},
    "relativeCreated": {"color": "green"},
    "msecs": {"color": "green"},
}
# FIELD STYLES FOR ALERT LEVEL
STREAM_ALERT_FIELD_STYLES = {
    "lineno": {"color": "red"},
    "name": {"color": "black"},
    "levelname": {"color": "black", "bold": True, "bright": True},
    "funcName": {"color": "black"},
    "asctime": {"color": "green"},
    "message": {"color": "white"},
    "filename": {"color": "black"},
    "module": {"color": "blue"},
    "relativeCreated": {"color": "green"},
    "msecs": {"color": "green"},
}

# DEFAULT LEVEL STYLES
STREAM_DEFAULT_LEVEL_STYLES = {
    "info": {"color": "green", "bold": False},
    "warning": {"color": "yellow", "bold": True},
    "error": {"color": 196, "bold": False},
    "debug": {"color": 27, "bald": True},
    "critical": {"color": "white", "bold": True, "background": "red"},
    "exception": {"color": 196, "bold": True},
    "alert": {"color": 166, "bold": True},
    "important": {"color": 40, "bold": True},
    "user_input": {"color": 200, "bold": True},
    "message": {"bold": True},
    "action_required": {"color": 99, "bold": True},
}
# DEFAULT COMSOLE LOG FORMAT
LOG_DEFAULT_FORMAT = (
    "|%(asctime)s|%(levelname)s|   %(message)s   |%(filename)s|%(funcName)s|%(lineno)d"
)
PERF_LOG_DEFAULT_FORMAT = "|%(asctime)s|%(levelname)s|   %(message)s"
# FORMAT FOR ALERT LEVEL
LOG_LESSINFO_FORMAT = "|%(asctime)s|%(levelname)s|   %(message)s"
DEFAULT_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

# find the parent directory of the current file
root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DEFAULT_FILE_LOG_DIR = os.path.join(root_path, "logs")


# Class ConsoleLogger returns a logger for class calling it, logger is logging only to console,
# with different styles
# class ConsoleLogger has custom methods for logging at different levels
# inspect.stack() will be used to get correct caller name, line number, file name, function name etc


class CustomLogger:
    """Custom Logger class"""

    def __init__(
        self,
        log_level=DEFAULT_LOG_LEVEL,
        log_name=DEFAULT_LOG_NAME,
        field_styles=STREAM_DEFAULT_FIELD_STYLES,
        level_styles=STREAM_DEFAULT_LEVEL_STYLES,
        log_format=LOG_DEFAULT_FORMAT,
        time_format=DEFAULT_TIME_FORMAT,
        log_dir=DEFAULT_FILE_LOG_DIR,
        enable_stream=True,
    ):
        self.enable_stream = enable_stream
        self.log_level = log_level
        self.log_name = log_name
        self.field_styles = field_styles
        self.level_styles = level_styles
        self.log_format = log_format
        self.time_format = time_format
        self.file_log_dir = log_dir
        self.logger = logging.getLogger(self.log_name)
        logging.addLevelName(35, "ALERT")
        logging.addLevelName(25, "IMPORTANT")
        logging.addLevelName(45, "EXCEPTION")
        logging.addLevelName(200, "MESSAGE")
        logging.addLevelName(150, "ACTION_REQUIRED")
        logging.addLevelName(15, "USER_INPUT")
        self.logger.setLevel(self.log_level)

        if self.enable_stream:
            self.stream_handler = logging.StreamHandler()
            self.stream_handler.setLevel(self.log_level)
            self.stream_formatter = coloredlogs.ColoredFormatter(
                fmt=self.log_format,
                field_styles=self.field_styles,
                level_styles=self.level_styles,
                datefmt=self.time_format,
            )
            self.stream_handler.setFormatter(self.stream_formatter)
            self.logger.addHandler(self.stream_handler)
        self.logger.propagate = False
        # file handler variables
        self.file_handler = None
        self.create_log_folder()
        self.create_file_handler()

    # create log folder if not exists
    def create_log_folder(self, log_dir=DEFAULT_FILE_LOG_DIR):
        """Creates log folder if not exists"""
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    # create_file_handler method creates a file handler for logger and adds it to logger
    # checks if file handler already exists, if yes, removes it and creates a new one
    # checks if directory or file exists, if not, creates them, adds date to file name

    def create_file_handler(self):
        """Creates file handler"""
        if self.file_handler:
            self.logger.removeHandler(self.file_handler)
        if not os.path.exists(self.file_log_dir):
            os.makedirs(self.file_log_dir)
        self.file_handler = logging.handlers.RotatingFileHandler(
            os.path.join(
                self.file_log_dir,
                self.log_name
                + "_"
                + datetime.datetime.now().strftime("%Y-%m-%d")
                + ".log",
            ),
            maxBytes=10485760,
            backupCount=10,
            encoding="utf-8",
        )
        self.file_handler.setLevel(self.log_level)
        self.file_formatter = logging.Formatter(
            fmt=self.log_format, datefmt=self.time_format
        )
        self.file_handler.setFormatter(self.file_formatter)
        self.logger.addHandler(self.file_handler)

    # set colored formatter to default format
    def set_default_formatter(self):
        """Sets default logging format"""
        self.stream_formatter = coloredlogs.ColoredFormatter(
            fmt=LOG_DEFAULT_FORMAT,
            field_styles=self.field_styles,
            level_styles=self.level_styles,
            datefmt=self.time_format,
        )
        self.stream_handler.setFormatter(self.stream_formatter)

    # set new format for colored formatter for specific level
    def set_colored_formatter_format(self, log_format):
        """Sets default color format

        Args:
            log_format (str): log format
        """
        self.log_format = log_format
        self.stream_formatter = coloredlogs.ColoredFormatter(
            fmt=self.log_format,
            field_styles=self.field_styles,
            level_styles=self.level_styles,
            datefmt=self.time_format,
        )
        self.stream_handler.setFormatter(self.stream_formatter)

    # set new formatter for specific level
    def set_formatter(self, level, log_format, time_format):
        """Sets log format"""
        self.log_format = log_format
        self.time_format = time_format
        self.stream_formatter = logging.Formatter(
            fmt=self.log_format, datefmt=self.time_format
        )
        self.stream_handler.setFormatter(self.stream_formatter)
        self.logger.setLevel(level)
        self.stream_handler.setLevel(level)

    # set new log level
    def set_level(self, level):
        """Sets level"""
        self.logger.setLevel(level)
        self.stream_handler.setLevel(level)

    # set new log name
    def set_name(self, name):
        """Sets log name

        Args:
            name (str): Log Name
        """
        self.log_name = name
        self.logger = logging.getLogger(self.log_name)

    # creates new record for logger with file name, function name, line number, message, level etc
    # addes exception type error to record if exception is passed
    def create_record(self, msg, level, exception=None):
        """Creates new log record"""
        stack = inspect.stack()
        record = logging.LogRecord(
            name=self.log_name,
            level=level,
            pathname=stack[2][1],
            lineno=stack[2][2],
            msg=msg,
            args=None,
            exc_info=exception,
            func=stack[2][3],
        )
        return record

    def info(self, msg):
        """Info"""
        record = self.create_record(msg, logging.INFO)
        self.logger.handle(record)

    def warning(self, msg):
        """Warning"""
        record = self.create_record(msg, logging.WARNING)
        self.logger.handle(record)

    def error(self, msg):
        """Error"""
        record = self.create_record(msg, logging.ERROR)
        self.logger.handle(record)

    def debug(self, msg):
        """Debug"""
        record = self.create_record(msg, logging.DEBUG)
        self.logger.handle(record)

    def critical(self, msg):
        """Critical"""
        record = self.create_record(msg, logging.CRITICAL)
        self.logger.handle(record)

    def important(self, msg):
        """Important"""
        record = self.create_record(level=25, msg=msg)
        self.set_colored_formatter_format(LOG_LESSINFO_FORMAT)
        self.logger.handle(record)
        self.set_default_formatter()

    def perflog(self, _time, _size, name):
        """Writes performance log"""
        msg = f"{name} | Human Duration: {humanize.naturaldelta(_time)} | Human Size: {humanize.naturalsize(_size)} | ({_time},{_size})"
        record = self.create_record(msg, logging.INFO)
        self.logger.handle(record)

    # exception level is used for logging exceptions
    # prints exception type, exception message
    def exception(self, msg):
        """Exception"""
        record = self.create_record(level=45, msg=msg, exception=sys.exc_info())
        self.logger.handle(record)

    # alert level is used for logging alerts with different style format
    def alert(self, msg):
        """Alert"""
        record = self.create_record(level=35, msg=msg)
        # change output format for alert level
        self.set_colored_formatter_format(LOG_LESSINFO_FORMAT)
        self.logger.handle(record)
        # change output format back to default
        self.set_default_formatter()

    def user_input(self, msg):
        """User Input"""
        record = self.create_record(level=15, msg=msg)
        self.logger.handle(record)

    def message(self, msg):
        """Message"""
        record = self.create_record(level=200, msg=msg)
        self.set_colored_formatter_format(LOG_LESSINFO_FORMAT)
        self.logger.handle(record)
        self.set_default_formatter()

    def action_required(self, msg):
        """Action Required"""
        record = self.create_record(level=150, msg=msg)
        self.logger.handle(record)


def main():
    """Main Function"""
    logger = CustomLogger()
    logger.create_file_handler()
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.alert("This is an alert message")
    logger.important("This is an important message")
    logger.error("This is an error message")
    logger.debug("This is a debug message")
    logger.critical("This is a critical message")
    logger.user_input("This is an input required message")
    logger.message("This is a message")
    logger.user_input("This is an input required message")
    logger.action_required("This is an action required message")

    try:
        1 / 0
    except BaseException:
        logger.exception("There is an exception")


perLogger = CustomLogger(
    log_name="Perf_Log", log_format=PERF_LOG_DEFAULT_FORMAT, enable_stream=False
)
systemLogger = CustomLogger(log_name="System_Log", enable_stream=False)


if __name__ == "__main__":
    main()
