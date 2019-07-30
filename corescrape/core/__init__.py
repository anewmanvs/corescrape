"""
Defines the base class for this package.

Imports log operator and takes a log or None
"""

from .. import logs

# pylint: disable=too-few-public-methods

class CoreScrape:
    """CoreScrape base class."""

    def __init__(self, logoperator=None):
        """Constructor."""

        self.logoperator = logoperator

        condition = (
            self.logoperator is not None and
            not isinstance(self.logoperator, logs.log_operator.LogOperator)
        )

        if condition:
            raise TypeError("Param 'logoperator' must be a 'LogOperator'")

    def __log(self, msg, tmsg=None):
        """Safely writes into log."""

        if self.logoperator:
            self.logoperator.comm(msg, tmsg)
