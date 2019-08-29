"""
Core Scrape Threading

Thread control for this package.
"""

from warnings import warn
from queue import Queue
from threading import Thread

from . import corescrape_event
from core import CoreScrape

# pylint: disable=invalid-name, too-few-public-methods, multiple-statements
# pylint: disable=bare-except

class CoreScrapeThread(CoreScrape):
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

    def __iterate(self, threadid, data, *args):
        """Do iterations in threads, each one calling the passed code."""

        # pylint: disable=unused-argument

        self.log('Starting iteration in threadid {} for {} items'.format(
            threadid, len(data)))
        res = []
        for url in data:
            # the reason here does not matter. If it is set, break out
            if self.event.is_set(): break

            try:
                page = self.rotator.request(url, self.event, threadid=threadid)
            except:
                self.event.state.set_ABORT_THREAD()
                break

            if page is None: continue  # not able to retrieve the page

            if self.parser is None:
                res.append(page)
                self.log('Storing whole response for {}. Thread {}'.format(
                    url, threadid))
            elif page.status_code == 404:
                self.log('URL {} returned a 404. Thread {}'.format(url, threadid),
                         tmsg='warning')
                res.append({url: None})  # points it was collected but useless
            else:
                _res = self.parser.parse(page, threadid=threadid)
                if not _res:
                    self.log('URL {} could not be parsed. Thread {}'.format(
                        url, threadid))
                    continue  # no info collected, must go on
                self.log('URL {} collected. Thread {}'.format(url, threadid),
                         tmsg='header')
                res.append({url: _res})
        return res

    def start_threads(self, to_split_params, *fixed_args):
        """Starts threads."""

        def test_if_urls(p):
            return [a.startswith('http://') or a.startswith('https://') for a in p]

        # pylint: disable=no-value-for-parameter

        abort = self.__warn_wait_threads()
        if abort:
            return False

        if not all(test_if_urls(to_split_params)):
            raise ValueError('List of strings must begin with protocol')

        self.log('Starting threads for {} items'.format(len(to_split_params)))

        self.threads = []
        self.event.state.set_EXECUTING()
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
        finally:
            for thread in self.threads:
                thread.join()
            self.event.clear()
            self.threads = []

    def join_responses(self):
        """Join responses from the threads."""

        abort = self.__warn_wait_threads()
        if abort:
            return []

        res = []
        while not self.queue.empty():
            res += self.queue.get()
        return res

    def is_sentenced(self):
        """
        Informs if the thread controller is sentenced due to the last event state.
        """

        sentenced = self.event.state.is_sentenced()
        if sentenced:
            self.event.state.set_FINISHED()
        return sentenced
