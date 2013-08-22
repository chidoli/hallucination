from hallucination import ProxyFactory
from hallucination.models import Proxy
from multiprocessing import Pool

import getopt
import os, sys
import logging
import json

logger = logging.getLogger('hallucination')
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

config = {}

# FIXME: This is not a good design
url = 'http://translate.google.com'
proxy_factory = None


def testrun_request(proxy):
    # NOTE: For some reason, testrun_worker has problems of calling class-level
    # functions. It will produce an error message like following:
    # PicklingError: Can't pickle <type 'function'>: attribute lookup __builtin__.function failed
    
    # FIXME: Read 'timeout' from config

    proxy_factory.make_request(url, proxy=proxy, timeout=10)

def testrun_worker(proxy):
    try:
        logger.info('Test run: Fetching %s via %s' % (url, proxy))
        testrun_request(proxy)
    except Exception as e:
        logger.error(str(e))

def testrun(proxies):
    # FIXME: Read 'processes' from config
    pool = Pool(processes=8)
    pool.map(testrun_worker, proxies)


def create():
    proxy_factory.create_db()


def _import(file_path):
    """Imports a list of proxy servers from a text file."""
    proxy_factory.import_proxies(open(file_path, 'r'))


def export(file_path):
    """Exports the list of proxy servers to the standard output."""
    proxy_factory.export_proxies(open(file_path, 'w'))


def select():
    print proxy_factory.select(1)


def evaluate():
    """Selects proxy servers that have not been recently evaluated, and evaluates each of them."""
    testrun(proxy_factory.get_evaluation_targets())


def parse_config(file_name):
    raw_config = file(file_name, 'r').read()

    global config
    config = json.loads(raw_config)


def main():
    opts, args = getopt.getopt(sys.argv[1:], 'cti:x:sd:E', ['config='])

    rf = None
    params = []
    for o, a in opts:
        if o == '-c':
            rf = create
        elif o == '-t':
            rf = testrun
        elif o == '-i':
            rf = _import
            params = [a]
        elif o == '-x':
            rf = export
            params = [a]
        elif o == '-s':
            rf = select
        elif o == '-E':
            rf = evaluate

        elif o == '--config':
            parse_config(a)

        elif o == '-d':
            config['db_uri'] = 'sqlite:///%s' % a

    global proxy_factory
    proxy_factory = ProxyFactory(config=dict(
        db_uri=config['db_uri']),
        logger=logger
    )

    if rf != None:
        rf(*params)
    else:
        raise Exception('Runtime mode is not specified.')

if __name__ == '__main__':
    main()
