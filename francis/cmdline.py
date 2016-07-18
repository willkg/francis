import functools
import sys
import traceback

import click
import tabulate
import todoist

from francis import __version__
from francis.util import ConfigFileMissingError, get_config


USAGE = '%prog [options] [command] [command-options]'
VERSION = 'francis ' + __version__


def add_config(fun):
    @functools.wraps(fun)
    def _add_config(*args, **kwargs):
        try:
            cfg = get_config()
        except ConfigFileMissingError:
            click.echo('Config file is missing. Add a ~/.francisrc file with '
                       'your auth token in it.')
            click.echo('')
            click.echo('===')
            click.echo('AUTH_TOKEN=<token>')
            click.echo('===')
            click.echo('')
            raise click.Abort()

        return fun(cfg, *args, **kwargs)
    return _add_config


def display_project(proj):
    if not proj or proj.data.get('inbox_project'):
        return ''

    return proj['name']


def click_run():
    sys.excepthook = exception_handler
    cli(obj={})


@click.group()
def cli():
    pass


@cli.command(name='list')
@click.argument('query', nargs=-1)
@click.pass_context
@add_config
def list_cmd(cfg, ctx, query):
    """List items by date

    Examples:

    \b
    * francis list
    * francis list today
    * francis list tomorrow
    * francis list friday
    * francis list "july 22"
    * francis list "over due"

    """
    api = todoist.api.TodoistAPI(cfg['auth_token'])

    api.sync()

    if not query:
        query = ['today']

    resp = api.query(query)
    for item in resp:
        if item['type'] == 'overdue':
            item['query'] = 'Over due'

        click.echo(item['query'])

        if not item['data']:
            continue

        table = [
            ('pri', 'content', 'project_id', 'date_string', 'id')
        ]
        data = sorted(
            item['data'],
            key=lambda item: (item['due_date'], item.get('date_string'))
        )

        for task in data:
            table.append(
                (
                    task['priority'],
                    task['content'],
                    display_project(api.projects.get_by_id(task['project_id'])),
                    task['date_string'],
                    task['id'],
                )
            )

        click.echo(tabulate.tabulate(table[1:], headers=table[0]))


def exception_handler(exc_type, exc_value, exc_tb):
    click.echo('Oh no! Francis has thrown an error while trying to do stuff.')
    click.echo('Please write up a bug report with the specifics so that ')
    click.echo('we can fix it.')
    click.echo('')
    click.echo('https://github.com/willkg/francis/issues')
    click.echo('')
    click.echo('Here is some information you can copy and paste into the ')
    click.echo('bug report:')
    click.echo('')
    click.echo('---')
    click.echo('Francis: %s' % repr(__version__))
    click.echo('Python: %s' % repr(sys.version))
    click.echo('Command line: %s' % sys.argv)
    click.echo(
        ''.join(traceback.format_exception(exc_type, exc_value, exc_tb)))
    click.echo('---')
