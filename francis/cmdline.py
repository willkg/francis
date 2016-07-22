import datetime
import functools
import sys
import traceback

import click
import pendulum
import todoist

from francis import __version__
from francis.util import (
    ConfigFileMissingError,
    get_config,
    parse_date,
    prettytable,
)


USAGE = '%prog [options] [command] [command-options]'
VERSION = 'francis ' + __version__


class DoesNotExist(Exception):
    pass


class TooMany(Exception):
    pass


class Action:
    """Captures an action applied to a specific item

    The item is denoted by an item id and the sequence number. This lets us
    undo an action iff the sequence number is the same which implies that item
    has not changed since the action was applied.

    """
    def __init__(self, item, field, old_value, new_value):
        self.item_id = item['id']
        self.item_seq_no = item.data.get('seq_no')
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
        return 'H'
    return ''


def display_project(proj):
    if not proj or proj.data.get('inbox_project'):
        return ''

    return proj['name']


def get_project_by_name(api, name):
    try:
        return [p for p in api.projects.all() if p['name'].lower() == name.lower()][0]
    except IndexError:
        raise DoesNotExist


PRIORITIES = {
    'h': 4,
    'l': 1,
}
DEFAULT_PRIORITY = 1


def get_val(keyval):
    return keyval.split(':', 1)[1].strip()


def apply_changes(api, item, changes):
    """Applies a set of changes and generates a list of Actions applied"""
    history = []

    for change in changes:
        if change.startswith('pri'):
            new_val = get_val(change)
            new_val = PRIORITIES.get(new_val.lower()[0], DEFAULT_PRIORITY)
            history.append(Action(item, 'priority', item['priority'], new_val))
            item.update(priority=new_val)

        elif change.startswith('pro'):
            new_val = get_val(change)
            try:
                proj = get_project_by_name(api, new_val)
                history.append(Action(item, 'project', item['project_id'], new_val))
                item.move(proj['id'])
            except DoesNotExist:
                click.echo('ERROR: Project "%s" does not exist' % new_val)

        elif change.startswith('due'):
            new_val = get_val(change)
            try:
                # FIXME: Seems like we can send date strings:
                # https://support.todoist.com/hc/en-us/articles/205325931-Dates-and-Times
                # item.update(date_string=parse_date(new_val))
                item.update(date_string=new_val)
            except ValueError:
                click.echo('ERROR: "%s" is not a valid date' % new_val)

        elif change.startswith('done'):
            new_val = get_val(change)
            if new_val == '1':
                history.append(Action(item, 'completed', '0', '1'))
                item.complete()
            elif new_val == '0':
                history.append(Action(item, 'completed', '1', '0'))
                item.uncomplete()
            else:
                click.echo('ERROR: "%s" not a valid done value' % new_val)

        else:
            click.echo('ERROR: unknown change type')

    return history


def get_by_id_suffix(api, obj_id_suffix):
    # Based on GetByIdMixin.get_by_id
    objs = [
        obj for obj in api.items.state[api.items.state_name]
        if str(obj['id']).endswith(obj_id_suffix) or obj.temp_id.endswith(obj_id_suffix)
    ]
    if not objs:
        raise DoesNotExist
    if len(objs) == 1:
        return objs[0]
    raise TooMany


def click_run():
    sys.excepthook = exception_handler
    cli(obj={})


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Todoist cli for Will's devious purposes.

    This cli is intended to promote MAXIMUM EFFORT!

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


@cli.command(name='show')
@click.argument('ids', nargs=1)
@click.pass_context
@add_config
def show_cmd(cfg, ctx, ids):
    """Shows one or more items"""
    api = todoist.api.TodoistAPI(cfg['auth_token'])
    api.sync()

    for item_id in ids.split(','):
        try:
            item = get_by_id_suffix(api, item_id)
            click.echo('id:       %s' % item['id'])
            click.echo('priority: %s' % display_priority(item['priority']))
            click.echo('content:  %s' % item['content'])
            click.echo('project:  %s' % display_project(api.projects.get_by_id(item['project_id'])))
            click.echo('due:      %s' % item['date_string'])
        except DoesNotExist:
            click.echo('"%s" does not exist.' % item_id)
        except TooMany:
            click.echo('"%s" matches multiple items.' % item_id)


@cli.command(name='deferall')
@click.pass_context
@add_config
def deferall_cmd(cfg, ctx):
    """Defers all of today's tasks to tomorrow

    Note: This is "nuclear" in the sense that it goes and changes
    EVERYTHING DUE TODAY. Don't use it if you're squeamish!

    """
    api = todoist.api.TodoistAPI(cfg['auth_token'])
    api.sync()

    # Note: This will only change things with a date string equal to today
    # formatted as "MMM DD". It won't cover recurring tasks or other things.
    today = datetime.date.today().strftime('%b %d')

    history = []
    for item in api.items.state[api.items.state_name]:
        if item['date_string'] == today:
            history.extend(apply_changes(api, item, ['due:tomorrow']))

    api.commit()
    click.echo('Done!')


def _add(api, mods):
    kwargs = {
        'date_string': 'today'
    }
    project_id = get_project_by_name(api, 'Inbox')
    text = []

    for item in mods:
        if item.startswith('pri') and ':' in item:
            val = get_val(item)
            try:
                kwargs['priority'] = PRIORITIES[val.lower()[0]]
            except KeyError:
                click.echo('ERROR: pri "%s" does not exist. Try H or L.' % val)
                raise click.Abort()

        elif item.startswith('proj') and ':' in item:
            val = get_val(item)
            try:
                project_id = get_project_by_name(api, val)['id']
            except DoesNotExist:
                click.echo('ERROR: "%s" is not a project.' % val)
                raise click.Abort()
        elif item.startswith('due') and ':' in item:
            val = get_val(item)
            kwargs['date_string'] = val
        else:
            text.append(item)

    if not text:
        click.echo('ERROR: No task summary text.')
        raise click.Abort()

    text = ' '.join(text)
    return api.items.add(text, project_id, **kwargs)


@cli.command(name='add')
@click.argument('mods', nargs=-1)
@click.pass_context
@add_config
def add_cmd(cfg, ctx, mods):
    """Add a new task

    Examples:

    \b
    * francis add new item
    * francis add proj:Work pri:H tweak the befunge valve to hot
    * francis add "gotta make $$$!"

    """
    api = todoist.api.TodoistAPI(cfg['auth_token'])
    api.sync()

    item = _add(api, mods)

    api.commit()
    click.echo('Task created #%s: %s.' % (item['id'], item['content']))
    click.echo('Done!')


@cli.command(name='log')
@click.argument('mods', nargs=-1)
@click.pass_context
@add_config
def log_cmd(cfg, ctx, mods):
    """Adds a task and marks it complete in one step"""
    api = todoist.api.TodoistAPI(cfg['auth_token'])
    api.sync()

    item = _add(api, mods)

    api.commit()

    history = []
    history.extend(apply_changes(api, item, ['done:1']))

    api.commit()

    click.echo('Task logged #%s: %s.' % (item['id'], item['content']))
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
        try:
            item = get_by_id_suffix(api, item_id)
            history.extend(apply_changes(api, item, changes))
            click.echo('Applied changes to #%s: %s.' % (item['id'], item['content']))
        except DoesNotExist:
            click.echo('Task "%s" does not exist.' % item_id)
        except TooMany:
            click.echo('"%s" matches multiple items.' % item_id)

    # FIXME: Update history.

    api.commit()
    click.echo('Done!')


@cli.command(name='done')
@click.argument('ids', nargs=1)
@click.pass_context
@add_config
def done_cmd(cfg, ctx, ids):
    """Mark one or more items as done"""
    api = todoist.api.TodoistAPI(cfg['auth_token'])
    api.sync()

    history = []

    for item_id in ids.split(','):
        item = get_by_id_suffix(api, item_id)
        history.extend(apply_changes(api, item, ['done:1']))
        click.echo('Marked as done #%s: %s.' % (item['id'], item['content']))

    # FIXME: Update history.

    api.commit()
    click.echo('Done!')


@cli.command(name='today')
@click.pass_context
def today_cmd(ctx):
    """Shortcut for "francis list today"
    """
    ctx.invoke(list_cmd)


@cli.command(name='tomorrow')
@click.pass_context
def tomorrow_cmd(ctx):
    """Shortcut for "francis list tomorrow"
    """
    ctx.invoke(list_cmd, query=['tomorrow'])


@cli.command(name='thisweek')
@click.pass_context
def thisweek_cmd(ctx):
    """Shows this week"""
    MON, TUE, WED, THU, FRI, SAT, SUN = range(7)
    LOOKUP = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    today = datetime.date.today().weekday()
    days = ['today']
    if today not in (SAT, SUN):
        for i in range(today+1, FRI+1):
            # days.append('+%s day' % (i - today))
            days.append(LOOKUP[i])

    for day in days:
        ctx.invoke(list_cmd, query=[day])
        click.echo('')


@cli.command(name='timesheet')
@click.pass_context
@add_config
def timesheet_cmd(cfg, ctx):
    """Shows timesheet for the week"""
    api = todoist.api.TodoistAPI(cfg['auth_token'])
    api.sync()

    marker = pendulum.today()
    while marker.day_of_week != 0:
        marker = marker.add(days=-1)

    click.echo('Timesheet week of %s' % marker.strftime('%c'))
    click.echo('')

    for i in range(7):
        begin_time = marker.start_of('day').in_timezone('UTC')
        end_time = marker.end_of('day').in_timezone('UTC')

        activity = api.completed.get_all(
            since=begin_time.strftime('%Y-%m-%dT%H:%M'),
            until=end_time.strftime('%Y-%m-%dT%H:%M'),
            limit=50
        )

        click.echo('[%s: %s]' % (marker.strftime('%A (%Y-%m-%d)'), len(activity['items'])))
        click.echo('')
        table = [
            ('id', 'content', 'proj')
        ]
        for event in activity['items']:
            table.append(
                (
                    event['task_id'],
                    event['content'],
                    display_project(api.projects.get_by_id(event['project_id'])),
                )
            )

        table = prettytable(click.get_terminal_size()[0] - 2, table)
        for row in table.splitlines():
            click.echo('  ' + row)
        click.echo('')
        marker = marker.add(days=1)


@cli.command(name='overdue')
@click.pass_context
def overdue_cmd(ctx):
    """Shortcut for "francis list 'over due'"
    """
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
            ('id', 'pri', 'content', 'proj', 'due date')
        ]
        data = sorted(
            item['data'],
            key=lambda item: (item['due_date'], item.get('date_string'))
        )

        for task in data:
            table.append(
                (
                    task['id'],
                    display_priority(task['priority']),
                    task['content'],
                    display_project(api.projects.get_by_id(task['project_id'])),
                    task['date_string'],
                )
            )

        table = prettytable(click.get_terminal_size()[0], table)
        for i, line in enumerate(table.splitlines()):
            if i < 2:
                click.echo(line)
            elif i % 2 == 0:
                click.secho(line, fg='cyan', dim=True)
            else:
                click.echo(line)


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
