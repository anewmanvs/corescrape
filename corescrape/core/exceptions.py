"""
Core Scrape Exception Module

Implements corescrape exceptios for specific use in the package
"""

class CoreScrapeException(Exception):
    """CoreScrape base exception."""

    def __init__(self, msg):
        """Constructor."""

        self.msg = msg
        super().__init__(msg)

class CoreScrapeTimeout(CoreScrapeException):
    """Timeout exception."""

    def __init__(self):
        """Constructor."""

        super().__init__('Timeout limit reached')

class CoreScrapeInvalidProxy(CoreScrapeException):
    """Invalid proxy found."""

    def __init__(self):
        """Constructor."""

        super().__init__('Invalid proxy')
