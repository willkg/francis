import datetime
import os

import pendulum
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


def parse_date(text, relative_to=None):
    """Converts a date string into a datetime.date

    This is relative to the relative_to date which defaults to today.

    :arg text: the text to parse
    :arg relative_to: (optional) the datetime object to parse dates
        relative to

    :returns: Pendulum (subclass of datetime)

    :raises ValueError: if the text is not parseable

    """
    # First, if it's a date, try parsing it with pendulum--this doesn't require
    # a relative-to date.
    try:
        return pendulum.instance(datetime.datetime.strptime(text, '%Y-%m-%d'))
    except ValueError:
        pass

    if relative_to is None:
        relative_to = pendulum.today()
    else:
        relative_to = pendulum.instance(relative_to)

    # Match on lowercase messages
    text = text.lower()

    # Today and tomorrow
    if text.startswith('tod'):
        return relative_to
    if text.startswith('tom'):
        return relative_to.add(days=1)

    # Day of week; parsed as after today
    # (day of week is 0-based where 0 is a sunday)
    today_index = relative_to.day_of_week
    pairs = [
        ('sunday', 0),
        ('monday', 1),
        ('tuesday', 2),
        ('wednesday', 3),
        ('thursday', 4),
        ('friday', 5),
        ('saturday', 6)
    ]
    for day, offset in pairs:
        if day.startswith(text):
            adjustment = (offset - today_index) % 7
            print today_index, offset, adjustment
            return relative_to.add(days=adjustment)

    # FIXME: Other things to support from taskwarrior:
    # http://taskwarrior.org/docs/dates.html#names
    raise ValueError('"%s" is not parseable' % text)


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
    col_size = [len(str(col)) + 2 for col in rows[0]]
    for row in rows:
        for i, col in enumerate(row):
            col_size[i] = max(col_size[i], len(str(col)))

    # Adjust the width we're using. Need to remove 2 spaces for every column.
    width = width - (len(col_size) * 2)

    if sum(col_size) > width:
        # If the columns size is greater than the terminal width, we need to
        # shorten columns.
        if width < (len(col_size) * 2):
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

    elif sum(col_size) < width:
        # If the columns size is less than the terminal width, we need to
        # lengthen columns.

        # FIXME: This is a fudge factor that "makes it work", but I'm not clear
        # on why.
        width = width - 2

        # FIXME: We (abuse) knowledge of which is the content column and expand
        # that.
        if 'content' in rows[0]:
            content_index = rows[0].index('content')
            adj = width - (sum(col_size) - col_size[content_index])
            for row in rows:
                row[content_index] = row[content_index] + (' ' * (adj - len(row[content_index])))

    return tabulate.tabulate(rows, headers="firstrow")
