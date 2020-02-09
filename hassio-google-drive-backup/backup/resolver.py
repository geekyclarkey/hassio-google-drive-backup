import socket
from typing import Any, Dict, List

import aiodns
from aiohttp.resolver import AsyncResolver
from injector import inject, singleton

from .config import Config
from .settings import Setting

TTL_HOURS = 12


@singleton
class SubvertingResolver(AsyncResolver):
    @inject
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self._original_dns = self._resolver
        self.setAlternateResolver()

    # TODO: Add tests for this method
    async def resolve(self, host: str, port: int = 0,
                      family: int = socket.AF_INET) -> List[Dict[str, Any]]:
        # TODO: add readme for "How do I know this won't do anything sketchy" along the lines of Tron's FAQ.  Caveat Emptor, explain the environment (docker, images, etc) for peace of mind.
        if host == self.config.get(Setting.DRIVE_HOST_NAME) and len(self.config.get(Setting.DRIVE_IPV4)) > 0 and family == 0:
            # return the "mocked" drive address instead.
            return [{
                'family': 0,
                'flags': socket.AddressInfo.AI_NUMERICHOST,
                'port': port,
                'proto': 0,
                'host': self.config.get(Setting.DRIVE_IPV4),
                'hostname': host
            }]
        addresses = await super().resolve(host, port, family)
        return addresses

    def updateConfig(self):
        if self._alt_ns != self.config.get(Setting.ALTERNATE_DNS_SERVERS):
            self.setAlternateResolver()
            self._resolver = self._alt_dns

    def setAlternateResolver(self):
        if len(self.config.get(Setting.ALTERNATE_DNS_SERVERS)) > 0:
            self._alt_dns = aiodns.DNSResolver(loop=self._loop, nameservers=self.config.get(
                Setting.ALTERNATE_DNS_SERVERS).split(","))
        else:
            self._alt_dns = self._original_dns
        self._alt_ns = self.config.get(Setting.ALTERNATE_DNS_SERVERS)

    def toggle(self):
        if self._resolver == self._original_dns:
            self._resolver = self._alt_dns
        else:
            self._resolver = self._original_dns
