"""
Custom Page Parser.

Implements a custom page parser to be used as an example of how page parses can
be constructed in this project. We advise you to build your own parser.

Do parsing in a requests.model.Response to retrieve information based on informed
xpaths.
"""

import pgparser.simple_parser as sp

# pylint: disable=invalid-name, too-few-public-methods, multiple-statements

class CustomPageParser(sp.SimpleParser):
    """
    Custom Page Parser.

    Implements a custom page parser to be used as an example of how page parses can
    be constructed in this project. We advise you to build your own parser.

    Params:
        xpaths: dict - User defined keys to organize values, each one being a list
            of xpath (str) and function to filter information. The function should
            either be None or capable of filtering a list of str.
        logoperator: corescraper.logs.log_operator.LogOperator - Log object or None
            to manage logging messages. Default None
    """

    def __init__(self, xpaths, logoperator=None):
        """Constructor."""

        errmsg = (
            "Parameter 'xpaths' must be a dict, each value being a list "
            "containing an xpath (str) and a function to filter results (or None), "
            "organized by keys"
        )

        if not isinstance(xpaths, dict):
            raise ValueError(errmsg)

        for key in xpaths:
            if not isinstance(xpaths[key][0], str):
                raise ValueError(errmsg)
            if xpaths[key][1] is not None and not callable(xpaths[key][1]):
                raise ValueError(errmsg)

        self.xpaths = xpaths
        super().__init__(None, logoperator=logoperator)

        self.log('Started parser for xpaths {}'.format(self.xpaths))

    def parse(self, response, threadid=None):
        """From a request.model.Response, applies xpaths and retrieves data."""

        if not self.valid_response(response, threadid): return []

        res = {}
        for key in self.xpaths:
            hs = sp.html.fromstring(response.text).xpath(self.xpaths[key][0])
            hs = self.xpaths[key][1](hs)
            self.log('Collected {} info for key {} [Thread {}]'.format(
                len(hs), key, threadid))
            res[key] = hs
        return res if any(res.values()) else {}
