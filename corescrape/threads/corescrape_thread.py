"""
Core Scrape Threading

Thread control for this package.
"""

from warnings import warn
from queue import Queue
from threading import Thread

from numpy import ndarray

from . import corescrape_event
from .. import core

# pylint: disable=invalid-name, too-few-public-methods

class CoreScrapeThread(core.CoreScrape):
    """Core Scrape Thread."""

    def __init__(self, nthreads, rotator, parser=None, logoperator=None):
        """Constructor."""

        # inputs
        self.nthreads = nthreads
        self.actualnthreads = nthreads
        self.rotator = rotator
        self.parser = parser

        # control attrs
        self.queue = Queue()
        self.event = corescrape_event.CoreScrapeEvent(logoperator=logoperator)
        self.threads = []

        super().__init__(logoperator=logoperator)

    def __split(self, a):
        """
        Tries to split the input into chunks for each thread.

        Input must be a list.
        """

        if not isinstance(a, list):
            raise TypeError("Param 'a' must be 'list'")

        n = self.nthreads  # desired number of threads
        k, m = divmod(len(a), n)
        split = [a[i * k + min(i, m):(i + 1) * k + min(i + 1, m)] for i in range(n)]
        split = [part for part in split if part]  # drops empty chunks
        # actual number of threads. Sometimes differs from 'nthreads'
        self.actualnthreads = len(split)
        return split

    def __warn_wait_threads(self):
        """Produce warning to wait for threads if needed."""

        if self.threads:
            warn(
                'There are threads running. Wait for them to stop before calling '
                'this method'
            )
            return True
        return False

    def __iterate(self, threaid, data, *args):
        """Do iterations in threads, each one calling the passed code."""

    def start_threads(self, to_split_params, *fixed_args):
        """Starts threads."""

        # pylint: disable=no-value-for-parameter

        abort = self.__warn_wait_threads()
        if abort:
            return False

        self.threads = []
        for threadid, split in enumerate(self.__split(to_split_params)):
            pargs = (threadid, split, *fixed_args)
            thread = Thread(
                target=lambda q, *args: q.put(self.__iterate(*args)),
                args=(self.queue, *pargs)
            )
            thread.start()
            self.threads.append(thread)
        return True

    def wait_for_threads(self):
        """Wait lock for threads."""

        try:
            self.event.wait()
        except KeyboardInterrupt:
            self.event.state.set_ABORT_USER()
            self.event.set()
        finally:
            for thread in self.threads:
                thread.join()
            self.event.clear()

    def join_responses(self):
        """Join responses from the threads."""

        res = []
        while not self.queue.empty():
            res.append(self.queue.get())
        return res
