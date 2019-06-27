import os
import click
import re
import requests

from bmgr.client import Client
from ClusterShell.NodeSet import NodeSet
from texttable import Texttable


def parse_config(conf_path):
       try:
              exec(open(conf_path, 'r').read())
              return BMGR_CLIENT_URL
       except:
              raise click.ClickException('Unable to parse configuration file')

def get_client():
    base_url = os.environ.get('BMGR_CLIENT_URL', None)
    if base_url is None:
        conf_path = os.environ.get('BMGR_CONF_PATH', '/etc/bmgr/')
        conf_path = os.path.join(conf_path, 'bmgr.conf')
        base_url = parse_config(conf_path)

    return Client(base_url)


valid_identifier=r'^[A-Za-z0-9_\-\.]+$'

def validate_hosts(hosts):
    for h in hosts:
        if not re.match(valid_identifier, h):
            raise ValidationError('Invalid host identifier ({})'.format(h))

    return hosts

def validate_profiles(profiles):
    if profiles is None:
        return None

    if profiles:
        profiles = profiles.split(',')
    else:
        profiles = []

    for p in profiles:
        if not re.match(valid_identifier, p):
            raise ValidationError('Invalid profile identifier ({})'.format(p))

    return profiles

def validate_attrs(attrs):
    if not attrs:
        return None

    for a, _ in attrs:
        if not re.match(valid_identifier, a):
            raise ValidationError('Invalid attribute identifier ({})'.format(a))

    return attrs

def validate_resource(res):
    if not res:
        raise ValidationError('Empty resource identifier')

    if not re.match(valid_identifier, res):
        raise ValidationError('Invalid resource identifier ({})'.format(res))

    return res


def validate_alias(alias):
    if not alias:
        raise ValidationError('Empty alias identifier')

    if not re.match(valid_identifier, alias):
        raise ValidationError('Invalid alias identifier({})'.format(alias))

    return alias


class ValidationError(Exception):
    pass


def handle_exceptions():
    """Decorator for pretty printing exceptions
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except requests.HTTPError as e:
                try:
                    click.secho('ERROR - ' + e.response.json()['error'], fg='red', err=True)
                except:
                    click.secho(str(e), fg='red', err=True)
            except ValidationError as e:
                click.secho('ERROR - ' + str(e), fg='red', err=True)

        wrapper.__doc__ = func.__doc__
        return wrapper

    return decorator


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
def cli():
    """ Command line interface to the bmgr server """
    pass

@cli.group()
def host():
    """ List and manage hosts """
    pass

def print_host_list(host_list):
    table = Texttable()
    table.set_deco(Texttable.HEADER | Texttable.HLINES)
    table.set_cols_dtype(['t', 't'])
    table.set_cols_align(["l", "l"])
    table.add_rows([["Profiles",    "Hosts"]] +
                   [[','.join(h['profiles']), h['name']] for h in host_list])

    click.echo(table.draw())

@host.command(name='list')
@handle_exceptions()
def hosts_list():
    """ List hosts """
    c = get_client()
    host_list = c.get_hosts()
    print_host_list(host_list)


@host.command(name='add', short_help='Add hosts')
@click.option('-p', '--profiles', help='coma separated list of profiles', default=None)
@click.argument('nodeset', nargs=1, type=NodeSet)
@handle_exceptions()
def hosts_add(nodeset, profiles):
    """ Add hosts

Example usage:

bmgr host add --profiles profileA,profileB node[100-200]

"""
    c = get_client()

    c.add_hosts(validate_hosts(nodeset), validate_profiles(profiles))

@host.command(name='update', short_help='Update hosts')
@click.option('-p', '--profiles', help='coma separated list of profiles', default=None)
@click.argument('nodeset', nargs=1, type=str)
@handle_exceptions()
def hosts_update(nodeset, profiles):
    """ Update hosts

Example usage:

bmgr host update --profile profileX node[100-200]

"""
    c = get_client()

    c.update_hosts(nodeset, validate_profiles(profiles))

@host.command(name='del', short_help='Delete hosts')
@click.argument('nodeset', nargs=1, type=NodeSet)
@handle_exceptions()
def hosts_del(nodeset):
    """ Delete hosts

Example usage:

bmgr host del node[100-200]

"""
    c = get_client()

    c.del_hosts(nodeset)


@host.command(name='show', short_help='Display hosts')
@click.argument('nodeset', nargs=1, type=NodeSet)
@handle_exceptions()
def hosts_show(nodeset):
    """ Display hosts

Example usage:

bmgr host show node[100-101]

 """
    c = get_client()

    host_list =  c.get_hosts(nodeset)
    print_host_list(host_list)

@cli.group(short_help='List and manage profiles')
def profile():
    """ List and manage profiles

A profile has a weight and defines a set of attributes (key/values). A host can
be associated to several profiles. Attributes conflicts are resolved by profile
weight (highest weight wins).

"""
    pass

def print_profile_list(profiles_list):
    table = Texttable()
    table.set_deco(Texttable.HEADER | Texttable.HLINES)
    table.set_cols_dtype(['t', 'i', 't'])
    table.set_cols_align(['l', 'l', 'l'])
    table.add_rows([["Profile",  "Weight", "Attribute/Value"]] +
                   [[p['name'], p['weight'],
                     '\n'.join([click.style(k, bold=True) + ': ' + v for k,v in  p['attributes'].items()])] for p in
                    sorted(profiles_list, key=lambda x: x['weight'])])
    click.echo(table.draw())

@profile.command(name='list')
@handle_exceptions()
def profiles_list(short_help="List profiles"):
    """ List profiles

Example usage:

bmgr profile list

"""
    c = get_client()

    profiles_list = c.get_profiles()
    print_profile_list(profiles_list)

@profile.command(name='add', short_help='Add a profile')
@click.option('-w', '--weight', help='profile weight', nargs=1, type=int)
@click.option('-a', '--attr', help='set profile attribute (multiple options allowed)',
              multiple=True, nargs=2,
              type=click.Tuple([str, str]))
@click.argument('profile', nargs=1, type=str)
@handle_exceptions()
def profiles_add(weight, attr, profile):
    """ Add a profile

Example usage:

bmgr profile add compute --attr attr1 val1 --attr attr2 val2

"""
    c = get_client()
    c.add_profile(profile, validate_attrs(attr), weight)

@profile.command(name='update', short_help='Update a profile')
@click.option('-w', '--weight', help='profile weight', nargs=1, type=int)
@click.option('-a', '--attr', multiple=True, nargs=2,
              help='set profile attribute', type=click.Tuple([str, str]))
@click.option('-r', '--del-attr', multiple=True, nargs=1,
              help='delete profile attribute')
@click.argument('profile', nargs=1, type=str)
@handle_exceptions()
def profiles_update(weight, attr, del_attr, profile):
    """ Update a profile

Example usage:

bmgr profile update compute ---del-attr attr1 --attr attr3 val3

"""
    c = get_client()

    attr = list(attr)
    for d in del_attr:
        attr.append((d, None))

    c.update_profile(profile, validate_attrs(attr), weight)

@profile.command(name='show', short_help='Display a profile')
@click.argument('profile', nargs=1, type=str)
@handle_exceptions()
def profiles_show(profile):
    """ Show a profile

Example usage:

bmgr profile show profileA


"""
    c = get_client()

    p = c.get_profile(profile)
    print_profile_list([p])


@cli.group(short_help='List and manage resources')
def resource():
    """ List and manage resources

Resources are rendered from their associated template and the attributes which
each host inherits from its profiles.

"""
    pass


def print_resource_list(resources_list):
    table = Texttable()
    table.set_deco(Texttable.HEADER | Texttable.HLINES)
    table.set_cols_dtype(['t',  't'])
    table.set_cols_align(['l',  'l'])
    table.add_rows([["Resource",  "Template URI"]] +
                   [[r['name'], r['template_uri']] for r in resources_list])
    click.echo(table.draw())

@resource.command(name='list')
@handle_exceptions()
def resources_list():
    """ List resources

Example usage:

bmgr resource list

"""
    c = get_client()

    resources_list = c.get_resources()
    print_resource_list(resources_list)

@resource.command(name='add', short_help='Add a resource')
@click.argument('resource', nargs=1, type=str)
@click.argument('template', nargs=1, type=str)
@handle_exceptions()
def resources_add(resource, template):
    """ Add a resource

Example usage:

bmgr resource add ipxe_boot file://ipxe.jinja

"""
    c = get_client()
    c.add_resource(validate_resource(resource), template)


@resource.command(name='update', short_help='Update a resource')
@click.option('-t', '--template', nargs=1,
              help='Template URI')
@click.argument('resource', nargs=1, type=str)
@handle_exceptions()
def resources_update(template, resource):
    """ Update a resource

Example usage:

bmgr resource update ipxe_boot --template file://ipxe_new.jinja

 """
    c = get_client()
    c.update_resource(resource, template)


@resource.command(name='del', short_help='Delete a resource')
@click.argument('resource', nargs=1, type=str)
@handle_exceptions()
def resources_del(resource):
    """ Delete resources

Example usage:

bmgr resource del ipxe_boot

"""
    c = get_client()

    c.del_resource(resource)

@resource.command(name='render', short_help='Render resources')
@click.argument('resource', nargs=1, type=str)
@click.argument('host', nargs=1, type=str)
@handle_exceptions()
def resources_render(resource, host):
    """ Render resources

Render a resource for the specified host.

Warning: this will consume oneshot aliases

Example usage:

bmgr resource render ipxe_boot node100

"""
    c = get_client()
    click.echo(c.render_resource(resource, host))

@cli.group(short_help='List and manage aliases')
def alias():
    """ List and manage aliases

Aliases can be used to dynamically redirect hosts from one resource to
the other while keeping a fixed URL, for example to switch a 'boot'
resource between a 'disk' resource and a 'deploy' resource.

Aliases can be rendered for each host at the same URL as normal resources:

<api_url>/resources/<alias>/<host>

    """
    pass


def print_alias_list(aliases_list):
    table = Texttable()
    table.set_deco(Texttable.HEADER | Texttable.HLINES)
    table.set_cols_dtype(['t',  't'])
    table.set_cols_align(['l',  'l'])

    table.add_rows([["Alias",  "Target"]] +
                   [
                       [a['name'],
                        '\n'.join(['{}: * (default)'.format(click.style(a['target'], bold=True))] +
                                  ['{}: {}{}'.format(
                                      click.style(o['target'], bold=True),
                                      h,
                                      ' (oneshot)' if o['autodelete'] else '')
                                   for h, o in a['overrides'].items()])]
                       for a in aliases_list
                   ])
    click.echo(table.draw())

@alias.command(name='list', short_help="List aliases")
@handle_exceptions()
def aliases_list():
    """ List aliases """
    c = get_client()

    aliases_list = c.get_aliases()
    print_alias_list(aliases_list)

@alias.command(name='add', short_help='Add an alias')
@click.argument('alias', nargs=1, type=str)
@click.argument('target', nargs=1, type=str)
@handle_exceptions()
def aliases_add(alias, target):
    """ Add an alias

Example usage:

# Create a 'boot' alias redirecting to the 'normal_boot' resource

bmgr alias add boot normal_boot

"""
    c = get_client()
    c.add_alias(validate_alias(alias), target)

@alias.command(name='del', short_help='Delete an alias')
@click.argument('alias', nargs=1, type=str)
@handle_exceptions()
def aliases_del(alias):
    """ Delete an alias

Example usage:

bmgr alias delete boot

"""
    c = get_client()
    c.del_alias(alias)

@alias.command(name='override', short_help='Override an alias for some hosts')
@click.option('-o', '--oneshot', is_flag=True,
              help='One-time override applied on the next rendering')
@click.argument('alias', nargs=1, type=str)
@click.argument('hosts', nargs=1, type=NodeSet)
@click.argument('target', nargs=1, type=str)
@handle_exceptions()
def aliases_override(oneshot, alias, hosts, target):
    """ Override an alias for some hosts

Example usage:

# Redirect the 'boot' alias to the 'deploy_boot' resource for host[0-4]. The redirection is only applied once per host by using -o

bmgr alias override -o boot node[0-4] deploy_boot

"""
    c = get_client()
    c.add_override(alias, hosts, target, oneshot)

@alias.command(name='restore', short_help='Restore an alias for some hosts')
@click.argument('alias', nargs=1, type=str)
@click.argument('hosts', nargs=1, type=NodeSet)
@handle_exceptions()
def aliases_restore(alias, hosts):
    """ Restore an alias for some hosts

The resource rendered for the specified hosts is reverted to the default
resource configured for the alias.

Example usage:

bmgr alias restore boot node[0-4]

"""
    c = get_client()
    c.restore_alias(alias, hosts)


