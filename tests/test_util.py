import datetime

import pytest

from francis.util import (
    parse_date,
    parse_rc,
    prettytable,
)


class Test_parse_rc:
    def test_empty(self):
        assert parse_rc('') == {}

    def test_key_val(self):
        assert parse_rc('foo=bar') == {'foo': 'bar'}
        assert parse_rc('\n foo = bar ') == {'foo': 'bar'}

    def test_uppercase_key(self):
        assert parse_rc('FOO=bar') == {'foo': 'bar'}

    def test_multiple(self):
        assert parse_rc('foo=bar\nbaz=bat') == {'foo': 'bar', 'baz': 'bat'}

    def test_comments(self):
        assert parse_rc('# foo=bar') == {}
        assert parse_rc('  # foo=bar') == {}


class Test_prettytable:
    def test_empty(self):
        assert prettytable(0, []) == ''
        assert prettytable(100, []) == ''

    def test_single_row(self):
        assert (
            prettytable(100, [('a', 'b', 'c', 'd')]) ==
            (
                'a    b    c    d\n'
                '---  ---  ---  ---'
            )
        )

    def test_truncation(self):
        # Total width is under 50, so no changes get made
        assert (
            prettytable(50, [
                ('1', ('a' * 39) + 'b')
            ]) ==
            '1    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab\n'
            '---  ------------------------------------------'
        )
        # Total width is > 50, so all the c are truncated
        assert (
            prettytable(50, [
                ('1', ('a' * 41) + 'b' + 'cccccc')
            ]) ==
            '1    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab*\n'
            '---  ---------------------------------------------'
        )

    def test_numbers(self):
        # Total width is > 50, so all the c are truncated
        assert (
            prettytable(50, [
                (1, ('a' * 41) + 'b' + 'cccccc')
            ]) ==
            '1    aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab*\n'
            '---  ---------------------------------------------'
        )

    # FIXME: test multiple > 40 columns


class Test_parse_date:
    @pytest.mark.parametrize('text', [
        '2015-05-05',
        '2016-01-01'
    ])
    def test_datestamps(self, text):
        assert parse_date(text).strftime('%Y-%m-%d') == text

    @pytest.mark.parametrize('text,expected', [
        ('today', '2016-01-01'),
        ('tod', '2016-01-01'),
        ('tomorrow', '2016-01-02'),
        ('tom', '2016-01-02'),
    ])
    def test_today_tomorrow(self, text, expected):
        # This grounds relative dates to January 1st which was a Friday
        start = datetime.datetime(2016, 1, 1, 0, 0, 0)
        assert parse_date(text, relative_to=start).strftime('%Y-%m-%d') == expected

    @pytest.mark.parametrize('text,expected', [
        ('friday', '2016-01-01'),
        ('saturday', '2016-01-02'),
        ('sunday', '2016-01-03'),
        ('monday', '2016-01-04'),
        ('tuesday', '2016-01-05'),
        ('wednesday', '2016-01-06'),
        ('thursday', '2016-01-07'),
    ])
    def test_day_of_week(self, text, expected):
        # This grounds relative dates to January 1st which was a Friday
        start = datetime.datetime(2016, 1, 1, 0, 0, 0)
        assert parse_date(text, relative_to=start).strftime('%Y-%m-%d') == expected

    def test_value_error(self):
        with pytest.raises(ValueError):
            parse_date('2016-06-40')
