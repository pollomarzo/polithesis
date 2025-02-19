import datetime
import logging
import os
from functools import partial

import __main__
from tqdm import tqdm as std_tqdm

tqdm = partial(std_tqdm, dynamic_ncols=True)


class TqdmLoggingHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level)

    def emit(self, record):
        try:
            msg = self.format(record)
            std_tqdm.write(msg)
            self.flush()
        # except (KeyboardInterrupt, SystemExit):
        #     raise
        except Exception:
            self.handleError(record)


try:
    PREFIX = os.path.basename(__main__.__file__)
except:
    PREFIX = "ipythonNB"
    # main file not set by ipynb, no time to think of ergonomic solution

LOG_PATH = "../logs/"
LOG_NAME = f"{PREFIX}_{datetime.datetime.now().date()}"

logger = logging.getLogger(PREFIX)

logFormatter = logging.Formatter(
    "%(asctime)s [%(levelname)-5.5s]  %(message)s"  # [%(threadName)-12.12s]
)

tqdm_handler = TqdmLoggingHandler()
tqdm_handler.setFormatter(logFormatter)
logger.addHandler(tqdm_handler)

fileHandler = logging.FileHandler(
    "{0}/{1}.log".format(LOG_PATH, LOG_NAME),
    mode="a+",
)
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

# consoleHandler = logging.StreamHandler(sys.stdout)
# consoleHandler.setFormatter(logFormatter)
# logger.addHandler(consoleHandler)
logger.setLevel(logging.DEBUG)
logger.info("\n\n>>>>> start execution")
