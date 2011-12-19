#!/usr/bin/env python
#-*- coding:utf-8 -*-


"""

    URL scraper with TOR support, to dynamicly change IPs while scaping.
    This is useful in scenarios where you are ratelimited by IP.

    To run this you need:
    - torctl
    - pycurl
    - TOR running on 127.0.0.1:9050 with controlport 127.0.0.1:9051


    EXAMPLE:

    import torscrape

    urls = ["http://icanhazip.com/"]*10

    def my_handler(url, data):
        print url, data

    torscrape.process(urls, my_handler, refresh_ip=1, verbose=True)

    RANT:
    This would have been a perfect example to put in a class object.
    However, Python and multiprocessing does not play well with 
    stuff that you put in classes, making it completly impossible to
    make a nice OO-design.

    Also multiprocessing and keyboard interrupts make me cry.

"""

class _get_options:
    def __init__(self, url, handler, user_agent, tor_host, tor_port):
        self.url = url
        self.handler = handler
        self.user_agent = user_agent
        self.tor_host = tor_host
        self.tor_port = tor_port
    
def get(url, handler, user_agent="Mozilla/5.0", tor_host="127.0.0.1", tor_port=9050):

    try:
        import StringIO
        import pycurl 

        strio = StringIO.StringIO()

        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.PROXY, tor_host)
        c.setopt(pycurl.PROXYPORT, tor_port)
        c.setopt(pycurl.HTTPHEADER, ['User-agent: %s' % user_agent])
        c.setopt(pycurl.PROXYTYPE, pycurl.PROXYTYPE_SOCKS4)
        c.setopt(pycurl.WRITEFUNCTION, strio.write)
        c.perform()
        c.close()

        return handler(url, strio.getvalue())

    except KeyboardInterrupt:
        return

def _get_with_args(a):
    return get(a.url, a.handler, a.user_agent, a.tor_host, a.tor_port)

def change_ip(verbose=False):

    import time
    import os
    import sys
    from TorCtl import TorCtl

    if verbose: print "Renewing TOR route:", 
    sys.stdout.flush()
    torcontrol = TorCtl.connect()
    if torcontrol is None: raise TorNotReachableException()
    torcontrol.sendAndRecv("signal newnym\r\n")
    time.sleep(5)
    if verbose: print "done"
    sys.stdout.flush()
    # stupid function is sending output
    stdout = sys.stdout
    sys.stdout = open(os.devnull,"w")
    torcontrol.close()
    sys.stdout = stdout


def process(urls, handler, user_agent="Mozilla/5.0", tor_host="127.0.0.1", tor_port=9050, refresh_ip=10, threads=None, verbose=False):

    """ Processes a set of urls and dispatches them to a handler
        urls: a list of url strings
        handler: a function that accepts a string, which is the returned text
        user_agent: the user agent to use
        tor_host: tor host
        tor_port: tor port
        refresh_ip: refresh ip every NUM url fetches
        threads: use number of parallel threads
        verbose: be verbose
    """

    from multiprocessing import Pool
    import sys

    if threads:
        pool = Pool(threads, _init_worker)
    else:
        pool = Pool(initializer=_init_worker)

    if refresh_ip:
        paginated_urls = _paginate(urls, refresh_ip)
        for page in paginated_urls:
            change_ip(verbose)
            if verbose: print "Processing:", page
            packed_args = [_get_options(url, handler, user_agent, tor_host, tor_port) for url in page]
            try:
                pool.map(_get_with_args, packed_args)
            except KeyboardInterrupt:
                print "Wait for termination:",
                sys.stdout.flush()
                pool.terminate()
                print "done"
                sys.stdout.flush()
                break
    else:
        packed_args = [_get_options(url, handler, user_agent, tor_host, tor_port) for url in urls]
        try:
            pool.map(_get_with_args, packed_args)
        except KeyboardInterrupt:
            print "Wait for termination:",
            sys.stdout.flush()
            pool.terminate()
            print "done"
            sys.stdout.flush()

def _init_worker():
    import signal
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def _paginate(seq, rowlen):
    for start in xrange(0, len(seq), rowlen):
        yield seq[start:start+rowlen]

class TorNotReachableException(Exception):
    pass
