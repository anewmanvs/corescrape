"""
Core Scrape Threading

Thread control for this package.
"""

import signal
from warnings import warn
from queue import Queue
from threading import Thread

from . import corescrape_event
from core import CoreScrape
from core.exceptions import CoreScrapeTimeout

# pylint: disable=invalid-name, too-few-public-methods, multiple-statements
# pylint: disable=bare-except, too-many-arguments, too-many-instance-attributes

def alarm_handler(signum, frame):
    """Handles the alarm."""

    raise CoreScrapeTimeout

class CoreScrapeThread(CoreScrape):
    """
    Core Scrape Thread.

    Uses multiples threads to request pages and parse its content.
    A valid rotator must be passed to produce each request using a new proxy
    and make it less likely to be red flagged as a bot or scrapper by internet
    service providers. The user could pass a parser (CoreScrape class or custom
    class with a 'parse' method) to parse the response and avoid having the need
    to store the whole page for postprocessing.
    This controller also gives the user the option to set up a timer, in seconds,
    to raise a timeout. The timer is set if the user provided an integer to param
    'timeout' during 'start_threads' method processing. The timer is unset in
    'wait_for_threads' method.

    Params:
        nthreads: int. Desired number of threads. Once the method 'start_threads' is
            called, the controller will try to split the given input into chunks of
            number 'nthreads'. If it is not possible to split in 'nthreads' chunks,
            then the actual number of threads is available in 'actualnthreads'.
        rotator: corescrape.proxy.Rotator (preferably). Uses this rotator to make
            requests using different proxies and user agents. There is always the
            possibility to pass the 'requests' module to this parameter, but that is
            not advised as the control of proxies and user-agents is not automatic.
        parser: corescrape.pgparser.SimpleParser, based on or None. Uses this to
            parse the page content and extract the useful information, making it
            less memory expensive. If no argument is given, the thread controller
            will return a list of the full pages collected.
        timeout: int or None. Time in seconds to configure the timeout process.
            Set up a timer to raise an event and stop the threads once the time is
            reached.
        logoperator: corescrape.logs.LogOperator or None. Log to be fed with process
            runtime information.
    """

    def __init__(self, nthreads, rotator, parser=None, timeout=None,
                 logoperator=None):
        """Constructor."""

        if timeout is not None and not isinstance(timeout, int):
            raise TypeError("Param. 'timeout' must be 'int' or 'NoneType'")

        # inputs
        self.nthreads = nthreads
        self.actualnthreads = nthreads
        self.rotator = rotator
        self.parser = parser
        self.timeout = timeout  # CAREFUL! This is not timeout for requests
        self.timeoutset = False

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

    def __set_timeout(self):
        """
        If seconds for timeout were informed in the constructor, will set an alarm
        for timeout. Once timeout is reached, the iteration is broken and return
        as expected.
        """

        if self.timeout:
            signal.signal(signal.SIGALRM, alarm_handler)
            signal.alarm(self.timeout)
            self.log('CoreScrapeThread set the timeout for {} seconds.'.format(
                self.timeout), tmsg='info')
            self.timeoutset = True

    def __disarm_timeout(self):
        """Turn off the timeout."""

        if self.timeoutset:
            self.timeoutset = False
            signal.alarm(0)
            self.log('CoreScrapeThread disarmed the timeout.', tmsg='info')

    def __check_am_i_the_last(self):
        """Check if this thread is the last and if should set an event."""

        if self.queue.qsize() == 1:
            self.event.state.set_DUTY_FREE()

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

        self.__check_am_i_the_last()
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

        self.__set_timeout()

        return True

    def wait_for_threads(self):
        """Wait lock for threads."""

        try:
            self.event.wait()
        except KeyboardInterrupt:
            self.event.state.set_ABORT_USER()
        except CoreScrapeTimeout:
            self.event.state.set_TIMEOUT()
        finally:
            self.__disarm_timeout()
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
