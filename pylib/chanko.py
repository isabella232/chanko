# Copyright (c) 2012 Alon Swartz <alon@turnkeylinux.org>
#
# This file is part of Chanko
#
# Chanko is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import os

from cache import RemoteCache, LocalCache
from packages import get_uris, download_uris
from plan import Plan
from utils import makedirs

class Error(Exception):
    pass

class ChankoConfig(dict):
    def __init__(self, path):
        if not os.path.exists(path):
            raise Error("chanko config not found: " + path)

        self.required = ['release', 'architectures']
        self['plan_cpp'] = [] # optional

        self._parse(path)
        self._verify(self.required)

    def override(self, path):
        if os.path.exists(path):
            self._parse(path)
            self._verify(self.required)

    def _parse(self, path):
        for line in file(path).readlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            key, val = line.split("=", 1)
            val = val.strip()
            self[key.strip().lower()] = val.split(" ") if val else []

    def _verify(self, required):
        for req in self.required:
            if not self.has_key(req):
                raise Error("%s not specified in conf" % req)

            if not self[req]:
                raise Error("%s has no value in conf" % req)

    @property
    def ccurl_cache(self):
        home = os.environ.get('HOME')
        return os.path.join(home, '.ccurl/chanko', self.release[0])

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError, e:
            raise AttributeError(e)

class Chanko(object):
    """Top-level object of the chanko"""

    def __init__(self, base, config, architecture, plan_cpp=[]):
        self.base = base
        self.config = config
        self.architecture = architecture

        self.trustedkeys = os.path.join(self.config, 'trustedkeys.gpg')
        self.sources_list = os.path.join(self.config, 'sources.list')
        for f in (self.sources_list, self.trustedkeys):
            if not os.path.exists(f):
                raise Error("required file not found: " + f)

        self.archives = os.path.join(self.base, 'archives', self.architecture)
        makedirs(os.path.join(self.archives, 'partial'))

        plan_path = os.path.join(self.base, 'plan')
        self.plan = Plan(plan_path, self.architecture, plan_cpp)

        self.local_cache = LocalCache(self)
        self.remote_cache = RemoteCache(self)

    def get_package_candidates(self, packages, nodeps=False):
        if not self.remote_cache.has_lists:
            self.remote_cache.refresh()

        return get_uris(self, self.remote_cache, packages, nodeps)

    def get_packages(self, candidates=None, packages=None, nodeps=False):
        if packages:
            candidates = self.get_package_candidates(packages, nodeps)

        if not candidates:
            return False

        result = download_uris(candidates)
        if result:
            self.local_cache.refresh()

        return result

def get_chankos():
    base = os.getcwd()
    config = os.path.join(base, 'config')
    conf = ChankoConfig(os.path.join(config, 'chanko.conf'))
    conf.override(os.path.join(config, 'chanko.conf.local'))

    os.environ['CCURL_CACHE'] = conf.ccurl_cache

    chankos = []
    for arch in conf.architectures:
        plan_cpp = list(conf.plan_cpp)
        chanko = Chanko(base, config, arch, plan_cpp)
        chankos.append(chanko)

    return chankos

