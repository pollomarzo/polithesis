import logging
import __main__
import datetime
import sys
import os

CURRENT_MAIN = os.path.basename(__main__.__file__)


LOG_PATH = "../logs/"
LOG_NAME = f"{CURRENT_MAIN}_{datetime.datetime.now().date()}"


logFormatter = logging.Formatter(
    "%(asctime)s [%(levelname)-5.5s]  %(message)s"  # [%(threadName)-12.12s]
)
logger = logging.getLogger(CURRENT_MAIN)

fileHandler = logging.FileHandler(
    "{0}/{1}.log".format(LOG_PATH, LOG_NAME),
    mode="a",
)
fileHandler.setFormatter(logFormatter)
logger.addHandler(fileHandler)

consoleHandler = logging.StreamHandler(sys.stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.INFO)
logger.info("\n\n>>>>> start execution")
