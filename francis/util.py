import os


class ConfigFileMissingError(Exception):
    pass


def parse_rc(data):
    contents = {}
    for line in data.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        key, val = [mem.strip() for mem in line.split('=', 1)]
        contents[key.lower()] = val
    return contents


def get_config(path=None):
    if not path:
        path = os.path.expanduser('~/.francisrc')

    if not os.path.exists(path):
        raise ConfigFileMissingError

    with open(path, 'r') as fp:
        cfg = parse_rc(fp.read())

    return cfg
