"""
Event manager

Implements a basic event with states for thread control
"""

from sys import stdout
from traceback import print_exc
from inspect import getmembers
from threading import Event

from core import CoreScrape

# pylint: disable=invalid-name

class States(CoreScrape):
    """Feasible thread states."""

    STARTED = 1
    EXECUTING = 2
    REFRESH_PROXIES = 3
    ABORT_THREAD = 4
    ABORT_USER = 5
    FINISHED = 6
    RESTARTING = 7
    OUT_OF_PROXIES = 8

    def __init__(self, logoperator=None):
        """Constructor."""

        self.curstate = States.STARTED
        self.dstates = self.__dfeasible_states()
        # inverse of dstates
        self.setates = {self.dstates[k]: k for k in self.dstates}

        self.__add_methods()  # adds 'is_' and 'set_' methods

        super().__init__(logoperator=logoperator)

    def __dfeasible_states(self):
        """Dict of feasible states."""

        states = {}
        for member in getmembers(States):
            var = member[0]
            if not var.startswith('__') and not callable(getattr(self, var)):
                states.update({var: member[1]})
        return states

    def traceback(self):
        """Produce traceback if strictly necessary."""

        if self.curstate == States.ABORT_THREAD:
            print_exc(file=stdout)

    def __str__(self):
        """To String."""

        return '{}-{}'.format(self.curstate, self.setates[self.curstate])

    def __add_methods(self):
        """
        Dynamically adds 'is_' and 'set_' methods for all states.

        This method cannot be called previous to '__dfeasible_states'
        """

        for kstate in self.dstates:
            self.__add_is_method(kstate)
            self.__add_set_method(kstate)

    def __add_is_method(self, kstate):
        """Dynamically adds an 'is_' method to compare states."""

        def _is():
            """Dynamic state comparision."""

            return self.curstate == self.dstates[kstate]

        setattr(self, 'is_{}'.format(kstate), _is)

    def __add_set_method(self, kstate):
        """Dynamically adds an 'set_' method to set the current state."""

        def _set():
            """Dynamic set current state."""

            if kstate in self.dstates.keys():
                self.curstate = self.dstates[kstate]
                self.log('State changed to {}'.format(self))
                self.traceback()
                return True
            return False

        setattr(self, 'set_{}'.format(kstate), _set)


class CoreScrapeEvent(Event):
    """Core Scrape Event."""

    def __init__(self, logoperator=None):
        """Constructor."""

        super().__init__()  # this class is an event
        self.state = States(logoperator=logoperator)  # but it does have states
