from francis.util import (
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
