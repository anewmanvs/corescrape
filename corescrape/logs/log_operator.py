"""
Log Operator

Simple log operator that is passed to each module and collects log messages.
The user can set the verbose mode to output the content while running.

IMPORTANT:
This class can NEVER import from core.CoreScrape in the present version
"""

from os.path import dirname, abspath
from datetime import datetime

# pylint: disable=invalid-name

class LogOperator:
    """Log Operator."""

    def __init__(self, file=None, verbose=False):
        """Constructor."""

        self.filename = file if file else abspath(dirname(__file__)) + '/log.txt'
        self.__file = open(self.filename, 'w+')
        self.verbose = verbose
        self.buffer = ''
        self.count = 0
        self.dtformat = '%Y-%m-%d %H:%M:%s:%f'
        self.open = True

    @staticmethod
    def color(tmsg=None):
        """Returns the color for the message type informed."""

        ec = '\033[0m'
        if tmsg == 'warning':
            return '\033[93m', ec
        if tmsg == 'header':
            return '\033[95m', ec
        if tmsg == 'info':
            return '\033[92m', ec
        return '', ''

    def comm(self, msg, tmsg=None):
        """Communicate the informed message."""

        self.count += 1
        _msg = '[{}] {}: {}'.format(datetime.now().strftime(self.dtformat),
                                    self.count, msg)

        self.buffer += '{}\n'.format(_msg)
        self.__file.write(_msg + '\n')

        if self.verbose:
            colors = LogOperator.color(tmsg)
            print('{0}{2}{1}'.format(*colors, _msg))

    def close(self):
        """Close file."""

        if self.open:
            self.comm('Closing file')
            self.__file.close()
            self.open = False

    def __del__(self):
        """Del."""

        self.close()

    def __bool__(self):
        """Bool."""

        return self.open
