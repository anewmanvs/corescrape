"""
Proxy Rotator

Reads from an online public proxy API and stores the proxies in a rotation list.
The APIs often return the content in a single param JSON, each line being an
IP:PORT. Please store URLs for APIs in the file `apilist.txt`, each line containing
a single URL starting with protocol like 'https://'. Please note that the access
to this API is not covered by any proxy. So scrapi  ng the same API owners is not a
very good idea since they might use their own servers to locate you.

As well as proxies, this class also rotates user agents, if available. Servers can
identify bots, crawlers and spiders even using multiple proxies if a common pattern
of user agents is present. Reads from the file `usragnt.txt`, each line being an
user agent. Make sure the user agents are valid as this package DOES NOT VALIDATE
any user agent.

Usually when dealing with public domain IPs or non residential IPs you get blocked
oftenly as most proxy users do not take necessary precautions to avoid being
detected. This rotator uses a list of 'reserved messages' to identify when an IP is
blocked. Each domain will provide a singular way to reject your request: some give
a 404 code, others will return a HTML page with messages informing the deny.
The list of 'reserved messages' should be store in the file `ignoremsgs.txt`.
This file is critical and must be present with each line containing a message that,
if present in the HTML page, tells the rotator to dispose that proxy and carry on.
More sophisticated pages may return a captcha.

Single proxy API can also be used by configuring the file `apisingleproxy.txt`.
This type of API returns a single ip when requested, usually in JSON format. Along
with the informed api URL, the user must pass a function to correctly parse the
response.

All files must be located in the `conf/` dir.

IMPORTANT:
* Make sure you ALWAYS use ELITE proxies, otherwise you are exposed
"""

# pylint: disable=invalid-name, multiple-statements

from os.path import dirname, abspath
from random import choice, shuffle
from queue import PriorityQueue

import requests

from . import proxy as proxlib
from core import CoreScrape
from threads.corescrape_event import CoreScrapeEvent

# pylint: disable=too-many-instance-attributes, too-many-branches

def strip(l):
    """Strip strings from a list."""

    return list(map(lambda x: x.strip(), l))


class Rotator(CoreScrape):
    """
    This class implements a proxy rotation service for requests.

    Every request sent to this class will be dispatched through a proxy
    selected from a priority queue.
    Proxies are collected from the apis informed in the file.
    In order to work, before making requests the method `retrieve` must be
    called to collect proxies and organize them in a priority queue.
    Initially all proxies will be listed as normal but as their score change,
    one proxy can be up or downgraded to high/low priority, respectively.

    If no param is informed, the method will use default values. It is recommended
    to inform at least params 'confpath' and 'logoperator'.

    Params:
        confpath: str indicating where the configuration files are stored
        maxtriesproxy: int indicating the max number of tries one proxy will get
        timeout: int pointing max timeout used in recurrent requests
        logoperator: corescrape.logs.LogOperator to manage the logs
    """

    def __init__(self, confpath=None, maxtriesproxy=2, timeout=3, logoperator=None):
        """Constructor."""

        if confpath is None:
            conf = abspath(dirname(__file__) + '/..') + '/conf/{}.txt'
        else:
            conf = abspath(confpath)
            conf += '{}.txt' if conf.endswith('/') else '/{}.txt'

        with open(conf.format('apilist'), 'r') as _file:
            self.apilist = strip(_file.readlines())

        try:
            with open(conf.format('usragnt'), 'r') as _file:
                self.usragnts = strip(_file.readlines())
        except FileNotFoundError:
            self.usragnts = None

        with open(conf.format('ignoremsgs'), 'r') as _file:
            self.ignoremsgs = strip(_file.readlines())

        with open(conf.format('stdconf'), 'r') as _file:
            self.stdusrgnt = _file.read().strip()

        self.proxies = PriorityQueue()
        self.maxtriesproxy = maxtriesproxy
        self.timeout = timeout

        super().__init__(logoperator=logoperator)

    def __get_usr_agent(self):
        """Returns a random user agent."""

        if not self.usragnts:
            return {'User-Agent': self.stdusrgnt}

        return {'User-Agent': choice(self.usragnts)}

    def __get_proxy(self):
        """Returns a proxy from the priority list."""

        if self.proxies.empty():
            return None

        return self.proxies.get()

    @staticmethod
    def proxy_exceptions():
        """Returns proxy exceptions to filter in this class."""

        _excp = requests.exceptions

        return (_excp.ProxyError, _excp.Timeout)

    @staticmethod
    def conn_exceptions():
        """Returns connection exceptions to filter in this class."""

        _excp = requests.exceptions

        return (_excp.SSLError, _excp.InvalidHeader, _excp.ConnectionError)

    @staticmethod
    def comm_exceptions():
        """Returns communication exceptions to filter in this class."""

        _excp = requests.exceptions

        return _excp.ChunkedEncodingError

    def retrieve(self, sep='\n', parse_func=None, timeout=30):
        """
        Retrieve the content from the APIs.

        If needed, the user can pass a function to parse the content
        output. The function must take and return a list and will be called
        one time for each API listed in the file.

        This method replaces proxies each time called.

        Params:
            sep: str pointing the separator used to split the return content
                into proxies formatted like IP:PORT
            parse_fun: python function that returns a list
            timeout: int max time in seconds to wait for a response

        Returns:
            None
        """

        if not self.apilist:
            raise TypeError(
                'Api list invalid. Expected a file with each line being an URL')

        self.log('Starting collecting proxies. {}'.format(
            'Parse func: {}'.format(parse_func) if parse_func is not None
            else 'No parse func.'
        ))

        proxies = []
        for api in self.apilist:
            self.log('Collecting {}'.format(api))

            a = requests.get(api, headers=self.__get_usr_agent(), timeout=timeout)
            a = list(map(lambda x: x.strip(), a.text.split(sep)))

            if callable(parse_func):
                proxies += parse_func(a)
            else:
                proxies += a
            self.log('Collected {} proxies from {}'.format(len(a), api))

        ignore = ['', ' ', ':', ' : ', ' :', ': ']
        proxies = list({x for x in proxies if x not in ignore})
        shuffle(proxies)

        self.log('Queueing {} proxies'.format(len(proxies)))
        for proxy in proxies:
            p = proxlib.Proxy(proxy)
            if p: self.proxies.put(p)

    def request(self, url, event=None, threadid=None):
        """
        Make a request using a proxy selected from the priority queue and a
        random user agent if available.

        Params:
            url: str representation of a URL to access. URL must be escaped.
            event: object event to trigger interruptions between eventual threads
        """

        if threadid is not None and event is None:
            raise TypeError("Param 'event' cannot be 'NoneType' in threading")

        if event is None:
            event = CoreScrapeEvent()

        if not isinstance(event, CoreScrapeEvent):
            raise TypeError("Param 'event' must be 'CoreScrapeEvent'")

        self.log('Starting loop for {} [Thread {}]'.format(url, threadid))

        msgeventset = 'Event set. Breaking loop for {} [Thread {}]'.format(
            url, threadid)

        while True:
            if event.is_set():
                self.log(msgeventset)
                break

            page = None
            curproxy = self.__get_proxy()
            if not curproxy:
                self.log('No proxy. {}'.format(msgeventset))
                event.state.set_OUT_OF_PROXIES()
                break

            uagnt = self.__get_usr_agent()

            self.log('Trying proxy {} and agent {} [Thread {}]'.format(
                curproxy, list(uagnt.values())[0], threadid))

            try:
                page = requests.get(url, headers=uagnt,
                                    proxies=curproxy.requests_formatted(),
                                    timeout=self.timeout)
            except Rotator.proxy_exceptions():
                tries = curproxy.add_up_try()
                if tries < self.maxtriesproxy:
                    self.proxies.put(curproxy)
                    continue
            except Rotator.conn_exceptions():
                continue
            except Rotator.comm_exceptions():
                continue

            if page is not None:
                if page.status_code == 403:
                    # Forbidden code. It does not mean this proxy is useless, but
                    # for now the provider detected too much requests were made
                    # by it. We should down its priority and hope in the future,
                    # when it is used again, the provider whitelisted it.
                    self.log('Proxy {} forbidden (403) [Thread {}]'.format(
                        curproxy, threadid))
                    curproxy.down_priority(10)  # 10 points down for priority
                    self.proxies.put(curproxy)
                    continue

                if not any([ignmsg in page.text for ignmsg in self.ignoremsgs]):
                    # did not find any token pointing the ban of this proxy
                    self.log('{} collected [Thread {}]'.format(url, threadid))
                    curproxy.up_priority()
                    self.proxies.put(curproxy)
                    return page

            self.log('Disposing proxy {} [Thread {}]'.format(curproxy, threadid),
                     tmsg='warning')

        return None
