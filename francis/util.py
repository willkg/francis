import os

import tabulate


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


def prettytable(width, rows):
    if not rows:
        return ''

    # Convert rows to lists
    rows = [list(row) for row in rows]

    # Go through and make sure rows are all the same size and if not, pad them.
    row_size = 0
    for row in rows:
        row_size = max(row_size, len(row))
    for row in rows:
        row.extend([''] * (row_size - len(row)))

    # Initialize col_size with the length of each column in the first row
    col_size = [len(col) for col in rows[0]]
    for row in rows:
        for i, col in enumerate(row):
            col_size[i] = max(col_size[i], len(str(col)))

    # Adjust the width we're using. Need to remove 3 spaces for every column.
    width = width - (len(col_size) * 3)

    # If the columns size is greater than the terminal width, we need to
    # shorten columns.
    if sum(col_size) > width:
        if width < (len(col_size) * 4):
            # If the terminal width is less than the number of columns * 4,
            # then let's just minimize all the columns and call it a day.
            col_size = [4] * len(col_size)

        else:
            while sum(col_size) > width:
                # Find a column > 40 characters and reduce it.
                bigger_than_40 = [(i, col) for i, col in enumerate(col_size) if col > 40]
                if bigger_than_40:
                    i, col = bigger_than_40[0]
                    col_size[i] = col_size[i] - 1
                    continue

                # FIXME: All columns are less than 40, so we need to try
                # something different.
                break

        # FIXME: For long text columns, we don't want to truncate, we want to
        # wrap.
        # Now go through and truncate columns to the new col_size
        for row in rows:
            for i, col in enumerate(row):
                if len(str(col)) > col_size[i]:
                    row[i] = col[:col_size[i]-1] + '*'

    return tabulate.tabulate(rows, headers="firstrow")
