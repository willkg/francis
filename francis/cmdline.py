import functools
import sys
import textwrap
import traceback

import click
import todoist

from francis import __version__
from francis.util import ConfigFileMissingError, get_config, prettytable


USAGE = '%prog [options] [command] [command-options]'
VERSION = 'francis ' + __version__


class DoesNotExist(Exception):
    pass


class Action:
    """Captures an action applied to a specific item

    The item is denoted by an item id and the sequence number. This lets us
    undo an action iff the sequence number is the same which implies that item
    has not changed since the action was applied.

    """
    def __init__(self, item, field, old_value, new_value):
        self.item_id = item['id']
        self.item_seq_no = item['seq_no']
        self.field = field
        self.old_value = old_value
        self.new_value = new_value


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


def display_priority(pri):
    if pri == 4:
        return 'HIGH'
    return ''


def display_project(proj):
    if not proj or proj.data.get('inbox_project'):
        return ''

    return proj['name']


def get_project_by_name(api, name):
    try:
        return [p for p in api.projects if p['name'] == name][0]
    except IndexError:
        raise DoesNotExist


PRIORITIES = {
    'h': 4,
}
DEFAULT_PRIORITY = 1


def apply_changes(api, item, changes):
    """Applies a set of changes and generates a list of Actions applied"""
    history = []

    for change in changes:
        if change.startswith('pri'):
            new_val = change.split(':', 1)[1].strip()
            new_val = PRIORITIES.get(new_val.lower()[0], DEFAULT_PRIORITY)
            history.append(Action(item, 'priority', item['priority'], new_val))
            item.update(priority=new_val)
        elif change.startswith('pro'):
            new_val = change.split(':', 1)[1].strip()
            try:
                proj = get_project_by_name(api, new_val)
            except DoesNotExist:
                click.echo('ERROR: "%s" does not exist' % new_val)
            else:
                history.append(Action(item, 'project', item['project_id'], new_val))
                item.update(project=proj['id'])
        elif change.startswith('done'):
            new_val = change.split(':', 1)[1].strip()
            if new_val in (1, '1'):
                history.append(Action(item, 'completed', '0', '1'))
                item.complete()
            elif new_val in (0, '0'):
                history.append(Action(item, 'completed', '1', '0'))
                item.uncomplete()
            else:
                click.echo('ERROR: "%s" not a valid done value' % new_val)
        else:
            click.echo('ERROR: unknown change type')

    return history


def click_run():
    sys.excepthook = exception_handler
    cli(obj={})


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Todoist cli for Will's devious purposes.

    Note: If invoked without a COMMAND, this does "francis list today".

    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(list_cmd)


@cli.command(name='undo')
@click.pass_context
@add_config
def undo_cmd(cfg, ctx):
    api = todoist.api.TodoistAPI(cfg['auth_token'])
    api.sync()

    # FIXME: Get history, pop top item off, undo it
    # undo_item =
    # click.echo('undo item ...')
    api.commit()
    click.echo('Done!')


@cli.command(name='modify')
@click.argument('ids', nargs=1)
@click.argument('changes', nargs=-1)
@click.pass_context
@add_config
def modify_cmd(cfg, ctx, ids, changes):
    """Modify one or more items"""
    api = todoist.api.TodoistAPI(cfg['auth_token'])
    api.sync()

    history = []

    for item_id in ids.split(','):
        item = api.items.get_by_id(int(item_id))
        history.extend(apply_changes(api, item, changes))

    # FIXME: Update history.

    api.commit()
    click.echo('Done!')


@cli.command(name='done')
@click.argument('ids', nargs=1)
@click.pass_context
@add_config
def done_cmd(cfg, ctx, ids, changes):
    """Mark one or more items as done"""
    api = todoist.api.TodoistAPI(cfg['auth_token'])
    api.sync()

    history = []

    for item_id in ids.split(','):
        item = api.items.get_by_id(int(item_id))
        history.extend(apply_changes(api, item, ['done:1']))

    # FIXME: Update history.

    api.commit()
    click.echo('Done!')


@cli.command(name='today')
@click.pass_context
def today_cmd(ctx):
    """Shortcut for "francis list today"."""
    ctx.invoke(list_cmd)


@cli.command(name='overdue')
@click.pass_context
def overdue_cmd(ctx):
    """Shortcut for "francis list 'over due'"."""
    ctx.invoke(list_cmd, query=['over due'])


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

        click.echo('[%s]' % item['query'])
        click.echo('')

        if not item['data']:
            continue

        table = [
            ('pri', 'content', 'proj', 'due date', 'id')
        ]
        data = sorted(
            item['data'],
            key=lambda item: (item['due_date'], item.get('date_string'))
        )

        for task in data:
            table.append(
                (
                    display_priority(task['priority']),
                    task['content'],
                    display_project(api.projects.get_by_id(task['project_id'])),
                    task['date_string'],
                    task['id'],
                )
            )

        click.echo(prettytable(click.get_terminal_size()[0], table))


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
