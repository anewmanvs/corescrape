"""
Simple Parser

Do parsing in a requests.model.Response to retrieve information based on informed
xpath.
"""

import re

from lxml import html

from core import CoreScrape

# pylint: disable=invalid-name, multiple-statements

class SimpleParser(CoreScrape):
    """
    Simple Parser.

    Do parsing based on xpath and optionally applies a regex.

    Params:
        xpath: str indicating the xpath to collect info in HTML
        regex: str regex to be applied. Only catches info if search returs True based
            on this regex.
        rgflags: enum 'RegexFlag' from re. Pass multiple flags using bitwise (|)
    """

    def __init__(self, xpath, regex=None, rgflags=0, logoperator=None):
        """Constructor."""

        self.xpath = xpath
        self.regex = regex
        self.rgfgs = rgflags
        self.brg = bool(regex)

        super().__init__(logoperator=logoperator)

    def apply_bool_rg(self, h):
        """Internal controller to apply regex."""

        if self.brg:
            return re.search(self.regex, h, self.rgfgs) is not None
        return True

    def valid_response(self, response, threadid=None):
        """Test if response is valid."""

        if not response:
            self.log('Parser got invalid response [Thread {}]'.format(threadid))
            return False
        return True

    def parse(self, response, threadid=None):
        """From a requests.model.Response, applies the xpath and retrieves data."""

        if not self.valid_response(response, threadid): return []

        hs = html.fromstring(response.text).xpath(self.xpath)
        self.log('Collected {} from page using xpath {} [Thread {}]'.format(
            len(hs), self.xpath, threadid))
        hs = [h for h in hs if self.apply_bool_rg(h)]
        self.log('After regex, {} remaining [Thread {}]'.format(len(hs), threadid))
        return hs
