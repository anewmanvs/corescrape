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

# State "properties" ----
NONE = 0  # generic property. Means nothing.
# A sentenced state means there is no recover for the thread controller.
SENTENCED = 1
# A traceback state means it should produce traceback on the state is activated.
TRACEBACK = 2
# A set event state means the state will set the event
SETEVENT = 3
# State "properties" ----

IDX, IDX_SENTENCED, IDX_TRACEBACK, IDX_SETEVENT = range(4)  # Properties indexes

class States(CoreScrape):
    """Feasible thread states."""

    # state = [index, is_sentenced?, produce_traceback?, set_event?]
    STARTED = [1, NONE, NONE, NONE]
    EXECUTING = [2, NONE, NONE, NONE]
    REFRESH_PROXIES = [3, NONE, NONE, SETEVENT]
    ABORT_THREAD = [4, SENTENCED, TRACEBACK, SETEVENT]
    ABORT_USER = [5, SENTENCED, NONE, SETEVENT]
    FINISHED = [6, SENTENCED, NONE, NONE]
    TIMEOUT = [7, NONE, NONE, SETEVENT]
    OUT_OF_PROXIES = [8, NONE, NONE, SETEVENT]

    def __init__(self, event, logoperator=None):
        """Constructor."""

        self.event = event
        self.curstate = States.STARTED[0]
        self.dstates, self.properties = self.__dfeasible_states()
        # inverse of dstates
        self.setates = {self.dstates[k]: k for k in self.dstates}

        self.__add_methods()  # adds 'is_' and 'set_' methods

        super().__init__(logoperator=logoperator)

    def __dfeasible_states(self):
        """Dict of feasible states."""

        states = {}
        properties = {}
        for member in getmembers(States):
            var = member[0]
            if not var.startswith('__') and not callable(getattr(self, var)):
                states[var] = member[1][IDX]
                properties[member[1][IDX]] = member[1]


        # check if indexes are unique
        errmsg = (" Please check the class 'States' under 'corescrape.threads"
                  ".corescrape_event'")
        val = states.values()
        if len(val) != len(set(val)):
            raise ValueError("It appears the states are not unique." + errmsg)

        # check if properties are correctly set
        sizes = [len(x) for x in properties.values()]
        if min(sizes) != max(sizes):
            raise ValueError(
                "It appears the state properties have different sizes. " + errmsg)

        return states, properties

    def __check_prop(self, prop):
        """Returns a property from the current state."""

        return self.properties[self.curstate][prop]

    def set_event(self):
        """
        Set an event to communicate interruptioms between threads in case
        this applies to the current state.
        """

        if self.__check_prop(IDX_SETEVENT) == SETEVENT:
            self.event.set()

    def is_sentenced(self):
        """Return True if current state is sentenced to end the loop."""

        return self.__check_prop(IDX_SENTENCED) == SENTENCED

    def traceback(self):
        """Produce traceback if strictly necessary."""

        if self.__check_prop(IDX_TRACEBACK) == TRACEBACK:
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
        """Dynamically adds a 'set_' method to set the current state."""

        def _set():
            """Dynamic set current state."""

            if kstate in self.dstates.keys():
                self.curstate = self.dstates[kstate]
                self.log('State changed to {}'.format(self))
                self.set_event()
                self.traceback()
                return True
            return False

        setattr(self, 'set_{}'.format(kstate), _set)


class CoreScrapeEvent(Event):
    """Core Scrape Event."""

    def __init__(self, logoperator=None):
        """Constructor."""

        super().__init__()  # this class is an event
        self.state = States(self, logoperator=logoperator)  # but it has states
