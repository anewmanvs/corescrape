"""
Simple Parser

Do parsing in a requests.model.Response to retrieve information based on xpaths
informed.
"""

import re

from lxml import html

# pylint: disable=invalid-name

class SimpleParser:
    """
    Simple Parser.

    Do parsing based on xpath and optionally applies a regex.

    Params:
        xpath: str indicating the xpath to collect info in HTML
        regex: str regex to be applied. Only catches info if search returs True based
            on this regex.
        rgflags: enum 'RegexFlag' from re. Pass multiple flags using bitwise (|)
    """

    def __init__(self, xpath, regex=None, rgflags=0):
        """Constructor."""

        self.xpath = xpath
        self.regex = regex
        self.rgfgs = rgflags
        self.brg = bool(regex)

    def __apply_bool_rg(self, h):
        """Internal gauge to apply regex."""

        return self.brg and re.search(self.regex, h, self.rgfgs) is not None

    def parse(self, response):
        """From a requests.model.Response, applies the xpath and retrieves data."""

        if not response:
            return []

        hs = html.fromstring(response.text).xpath(self.xpath)
        return [h for h in hs if self.__apply_bool_rg(h)]
