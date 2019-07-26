"""
Proxy Rotator

Reads from an online public proxy API and stores the proxies in a rotation list.
The APIs often return the content in a single param JSON, each line being an IP:PORT.
Please store URLs for APIs in the file `apilist.txt`, each line containing a single
URL starting with protocol like 'https://'.

As well as proxies, this class also rotates user agents, if available. Servers can
identify bots, crawlers and spiders even using multiple proxies if a common pattern
of user agents is present. Reads from the file `usragnt.txt`, each line being an
user agent. Make sure the user agents are valid as this package DOES NOT VALIDATE
any user agent.

Usually when dealing with public domain IPs or non residential IPs you get blocked
oftenly as most proxy users do not take necessary precautions to avoid being
detected. This rotator uses a list of 'reserved messages' to identify when an IP is
blocked. Each domain will provide a singular way to reject your request: some give
a 404 code, others (majority) will return a HTML page with messages informing the
deny. The list of 'reserved messages' should be store in the file `ignoremsgs.txt`.
This file is critical and must be present with each line containing a message that,
if present in the HTML page, tells the rotator to dispose that proxy and carry on.
More sophisticated pages may return a captcha.

All files must be located in the `conf/` dir.

IMPORTANT:
* Make sure you ALWAYS use ELITE proxies, otherwise you are exposed
"""

# pylint: disable=invalid-name

from random import choice

import requests

class Rotator:
    """
    This class implements a proxy rotation service for requests.

    Every request sent to this class will be dispatched through a proxy
    selected from a priority list.
    Proxies are collected from the apis informed in the file.
    In order to work, before making requests the method `retrieve` must be
    called to collect proxies and organize them in a priority list.
    Initially all proxies will be listed as normal but as their score change,
    one proxy can be up or downgraded to high/low priority, respectively.
    """

    def __init__(self):
        """Constructor."""

        conf = '../conf/{}.txt'

        with open(conf.format('apilist'), 'r') as _file:
            self.apilist = _file.readlines()

        try:
            with open(conf.format('usragnt'), 'r') as _file:
                self.usragnts = _file.readlines()
        except FileNotFoundError:
            self.usragnts = None

        with open(conf.format('ignoremsgs'), 'r') as _file:
            self.ignoremsgs = _file.readlines()

        self.proxies = None

    def __get_usr_agent(self):
        """Returns a random user agent."""

        if not self.usragnts:
            return None

        return {'User-Agent': choice(self.usragnts)}

    def retrieve(self, sep='\n', parse_func=None):
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

        Returns:
            None
        """

        if not self.apilist:
            raise TypeError(
                'Api list invalid. Expected a file with each line being an URL')

        proxies = []
        for api in self.apilist:
            a = requests.get(
                api, headers=self.__get_usr_agent()).text.split(sep)

            if callable(parse_func):
                proxies += parse_func(a)
            else:
                proxies += a

        self.proxies = proxies
