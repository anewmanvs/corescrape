"""
Proxy

IMPORTANT:
* Make sure you ALWAYS use ELITE proxies, otherwise you are exposed
"""

# pylint: disable=invalid-name, too-many-instance-attributes

class Proxy:
    """Defines a proxy and its useful methods"""

    def __init__(self, address):
        """Constructor."""

        self.ready = False  # should always be the first

        self.address = address
        self.numtries = 0
        try:
            self.__ip, self.__port = address.split(':')
        except ValueError:
            print(address)
            raise

        self.priority = 10
        # Maximum number of hits on a row. After this, the up_priority will
        # instead be a 'down_priority' to avoid reusing too much the same proxy.
        self.max_on_a_row = 3
        self.on_a_row = 0  # number of hits on a row


        self.ready = True  # should always be the last

    def requests_formatted(self):
        """Returns the proxy in requests formatting."""

        return {protocol: self.address for protocol in ['http', 'https']}

    def add_up_try(self):
        """Add up a try"""

        self.numtries += 1
        self.down_priority()
        return self.numtries

    def up_priority(self, weight=1):
        """Set higher priority to this proxy"""

        if self.on_a_row > self.max_on_a_row:
            # Number of maximum hits reached. The informed weight is ignored here
            self.down_priority(self.max_on_a_row + 1)
            return

        if self.priority > 0:
            self.priority -= weight
            self.on_a_row += 1

    def down_priority(self, weight=1):
        """Set lower priority to this proxy"""

        self.priority += weight
        self.on_a_row = 0

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
