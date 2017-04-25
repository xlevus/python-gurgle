import os
import imp
import logging

logger = logging.getLogger(__name__)


def load_gurglefile(gurglefile):
    wd = os.path.dirname(gurglefile)
    os.chdir(wd)
    logger.debug('Changed working directory to %r', os.getcwd())

    logger.debug('Loading %r', gurglefile)
    module = imp.load_source('gurglefile', gurglefile)
    return module
