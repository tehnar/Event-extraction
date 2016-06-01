#!/usr/bin/env python3

import sys
import logging.config
import logging

from daemon.daemon3x import daemon

LOG_PATH = "tmp/web.log"


def log_exception(type, value, tb):
    logging.exception("Uncaught exception: {0}".format(str(value)))


class ExampleServerDaemon(daemon):
    def run(self):
        try:
            logging.config.dictConfig({
                "version": 1,
                "disable_existing_loggers": "False",
                "formatters": {
                    "standard": {
                        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
                    }
                },
                "handlers": {
                    "default": {
                        "level": "DEBUG",
                        "class": "logging.FileHandler",
                        "filename": LOG_PATH,
                        "formatter": "standard"
                    }
                },
                "loggers": {
                    "": {
                        "handlers": ["default"],
                        "level": "DEBUG",
                        "propagate": "True"
                    }
                }
            })
            logger = logging.getLogger(__name__)
            logger.info("Logging initialized. Creating application...")
            sys.excepthook = log_exception
            from web_ui import app
            app.run(host='0.0.0.0')
        except Exception as e:
            with open('/tmp/error_file.txt', 'w') as f:
                import traceback
                f.write(traceback.format_exc())
                f.write('\n')
                f.write(e)


if __name__ == '__main__':
    my_daemon = ExampleServerDaemon('/tmp/example_d.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            my_daemon.start()
        elif 'stop' == sys.argv[1]:
            my_daemon.stop()
        elif 'restart' == sys.argv[1]:
            my_daemon.restart()
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    else:
        print("usage: %s start|stop|restart" % sys.argv[0])
        sys.exit(2)
