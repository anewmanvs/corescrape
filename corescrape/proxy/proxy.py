"""
Proxy

IMPORTANT:
* Make sure you ALWAYS use ELITE proxies, otherwise you are exposed
"""

# pylint: disable=invalid-name

class Proxy:
    """Defines a proxy and its useful methods"""

    def __init__(self, address):
        """Constructor."""

        self.address = address
        self.numtries = 0
        try:
            self.__ip, self.__port = address.split(':')
            self.ready = True
        except ValueError:
            print(address)
            self.ready = False

        self.priority = 10

    def add_up_try(self):
        """Add up a try"""

        self.numtries += 1
        self.down_priority()

    def up_priority(self):
        """Set higher priority to this proxy"""

        if self.priority > 0:
            self.priority -= 1

    def down_priority(self):
        """Set lower priority to this proxy"""

        self.priority += 1

    def ip(self):
        """Returns the IP"""

        return self.__ip

    def port(self):
        """Returns the port"""

        return self.__port

    def num_tries(self):
        """Number of tries this proxy has made"""

        return self.numtries

    def __str__(self):
        """To string"""

        return self.address

    def __bool__(self):
        """Points if this proxy is ready"""

        return self.ready

    def __eq__(self, other):
        """Equality between two proxies"""

        return self.priority == other.priority

    def __lt__(self, other):
        """Less than two proxies"""

        return self.priority < other.priority
