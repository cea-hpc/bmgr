from flask import (
  Flask, Blueprint, jsonify, make_response, abort, request, g, current_app
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload, relationship, synonym, validates
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import UniqueConstraint, and_
from flask_expects_json import expects_json
from ClusterShell import NodeSet
from ClusterShell.NodeSet import NodeSet as nodeset

import subprocess, tempfile, os, stat, flask, json, jinja2, sys, itertools, time
import re

MAX_NODESET = 100000

bp = Blueprint('main', __name__)
db = SQLAlchemy()

host_profiles_table = db.Table('host_profiles',
                               db.Column('host_id', db.Integer,
                                         db.ForeignKey('hosts.id')),
                               db.Column('profile_id', db.Integer,
                                         db.ForeignKey('profiles.id'))
                               )

class Profile(db.Model):
  __tablename__ = 'profiles'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255), unique=True)
  weight = db.Column(db.Integer, default=0)
  _attributes = db.Column('attributes', db.String(8000))

  @property
  def attributes(self):
    return json.loads(self._attributes)

  @attributes.setter
  def attributes(self, value):
    self._attributes = json.dumps(value)

  attributes = synonym('_attributes', descriptor=attributes)

  def __init__(self, name, attributes={}, weight=0):
      self.name = name
      self._attributes = json.dumps(attributes)
      self.weight = weight

  def __repr__(self):
      return '<Profile %r>' % (self.name)

  def to_dict(self):
    return {'name': self.name,
            'attributes': self.attributes,
            'weight': self.weight}

  @classmethod
  def from_dict(cls, d):
    profile = cls(d['name'], d.get('attributes', {}), d.get('weight', 0))
    return profile

def json_abort(status, error):
  abort(make_response(jsonify(error=error), status))


def parse_template_uri(uri):
  m = re.match('file://(.*)', uri)
  if m is None:
    json_abort(400, 'Unable to parse template URI')

  return m.group(1)

class Host(db.Model):
  __tablename__ = 'hosts'
  id = db.Column(db.Integer, primary_key=True)
  hostname = db.Column(db.String(255), unique=True)

  profiles = relationship("Profile", backref="host",
                       secondary=host_profiles_table, order_by=Profile.weight)

  def __init__(self, hostname):
    self.hostname = hostname

  def __repr__(self):
    return '<Host %r>' % (self.hostname)

  def to_dict(self):
    return {'name': self.hostname,
            'profiles': [ p.name for p in self.profiles ]}

  @property
  def attributes(self):
    # TODO: We should look at deep merging
    r = {}
    for p in self.profiles:
      r.update(p.attributes)

    return r

  @classmethod
  def from_dict(cls, d):
    host = cls(d['name'])
    if 'profiles' in d:
      host.profiles = [ get_profile(p) for p in d['profiles'] ]

    return host

class Resource(db.Model):
  __tablename__ = 'resources'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255), unique=True)
  template_uri = db.Column(db.String(4096))

  @validates('template_uri')
  def validate_uri(self, key, template_uri):
    parse_template_uri(template_uri)
    return template_uri

  def __init__(self, name, template_uri):
    self.name = name
    self.template_uri = template_uri

  def __repr__(self):
      return '<Resource %r>' % (self.name)

  def to_dict(self):
    return {'name': self.name,
            'template_uri': self.template_uri}

  @classmethod
  def from_dict(cls, d):
    profile = cls(d['name'], d['template_uri'])
    return profile

class Alias(db.Model):
  __tablename__ = 'aliases'
  __table_args__ = (UniqueConstraint('name', 'host_id', name='uix_1'),)
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255))
  target_id = db.Column(db.Integer, db.ForeignKey('resources.id'))
  host_id = db.Column(db.Integer, db.ForeignKey('hosts.id'))
  autodelete = db.Column(db.Boolean)

  target = relationship("Resource", uselist=False)
  host = relationship("Host", uselist=False)

  def __init__(self, name, target, host, autodelete=False):
    self.name = name
    self.target = target
    self.host = host
    self.autodelete = autodelete

  def __repr__(self):
    return '<Alias %r>' % (self.name)

@bp.errorhandler(404)
def not_found(error):
  return make_response(jsonify({'error': 'Not found'}), 404)

@bp.errorhandler(405)
def unauthorized(error):
  return make_response(jsonify({'error': 'Unauthorized'}), 405)

@bp.errorhandler(409)
def conflict(error):
  return make_response(jsonify({'error': 'Conflict'}), 409)

def init_db():
  db.create_all()
  db.session.add(Resource('boot',
                          'file://boot.jinja'))
  db.session.add(Resource('deploy',
                          'file://deploy.jinja'))
  db.session.commit()


def get_profile(profile_name):
  try:
    p = db.session.query(Profile).filter_by(name=profile_name).one()
  except NoResultFound:
    json_abort(404, "Profile '{}' not found".format(profile_name))

  return p

def get_resource(resource_name):
  try:
    r = db.session.query(Resource).filter_by(name=resource_name).one()
  except NoResultFound:
    json_abort(404, "Resource '{}' not found".format(resource_name))

  return r

def get_alias(alias_name, hostname=None, allow_fail=False):
  try:
    a= db.session.query(Alias)
    if hostname:
      return a.join(Host).filter(and_(Alias.name==alias_name,
                                      Host.hostname==hostname)).one()
    else:
      return a.filter(and_(Alias.name==alias_name,
                           Alias.host==None)).one()
  except NoResultFound:
    if allow_fail:
      return None
    else:
      json_abort(404, "Alias '{}' not found".format(alias_name))

def render(tpl, context):
  path = parse_template_uri(tpl)
  return jinja2.Environment(loader = jinja2.FileSystemLoader(
      current_app.config['BMGR_TEMPLATE_PATH'])).get_template(path).render(
    context)

def delete_profile(name):
  p = get_profile(name)
  db.session.delete(p)

def query_hosts(host_list=None, check_count=False):
  hosts = db.session.query(Host).options(joinedload('profiles'))

  if host_list is not None:
      hosts = hosts.filter(Host.hostname.in_(host_list))
      if check_count and hosts.count() != len(host_list):
        json_abort(404, "Host not found")

  return hosts


def query_aliases(alias_name=None, host_list=None, check_count=False):
  aliases = db.session.query(Alias)

  if alias_name is not None:
    aliases = aliases.filter_by(name=alias_name)

  if host_list is not None:
    aliases = aliases.join(Host).filter(Host.hostname.in_(host_list))

  if alias_name and host_list and check_count:
      if aliases.count() != len(host_list):
        json_abort(404, "Alias or override not found")

  return aliases

def get_hosts_folded(host_list=None):
  hosts = query_hosts(host_list)
  folded_list = []
  for profiles, hosts in  itertools.groupby(hosts, lambda x: x.profiles):
    folded_list.append({
        'name': str(nodeset.fromlist([h.hostname for h in hosts])),
        'profiles': [ p.name for p in profiles ]})

  return folded_list

def delete_hosts(host_list):
  db_hosts = query_hosts(host_list, check_count=True)

  for dbh in db_hosts:
    db.session.delete(dbh)

def get_host(hostname):
  """ Returns a single Host """
  try:
    return query_hosts([hostname]).one()
  except NoResultFound:
    json_abort(404, "Host '{}' not found".format(hostname))

@bp.route('/api/v1.0/hosts', methods=['POST'])
@expects_json({
  'type': 'object',
  'properties': {
    'name': {'type': 'string'},
    'profiles': {'type': 'array', 'items': {'type': 'string'}},
  },
  'required': ['name']
})
def api_hosts_post():
  db_hosts = []
  t0 = time.time()
  try:
    host_list = nodeset(g.data['name'])
    if len(host_list) > MAX_NODESET:
      json_abort(413, "Nodeset too large")

    for i, host in enumerate(host_list):
      single_host = g.data
      single_host['name'] = host
      db_host = Host.from_dict(single_host)
      db.session.add(db_host)
      if i%1000 == 0:
        db.session.flush()

    db.session.commit()
  except SQLAlchemyError:
    # FIXME: Discriminate errors
    json_abort(409, "Host already exists")

  folded_hosts = get_hosts_folded(host_list)
  return jsonify(folded_hosts)

@bp.route('/api/v1.0/hosts', methods=['GET'])
def api_hosts_get():
  return jsonify(get_hosts_folded())

@bp.route('/api/v1.0/hosts/<string:hostname>', methods=['DELETE'])
def api_hosts_hostname_delete(hostname):
  delete_hosts(nodeset(hostname))
  db.session.commit()
  return make_response(jsonify([]), 204)

@bp.route('/api/v1.0/hosts/<string:hostname>', methods=['PATCH'])
@expects_json({
  'type': 'object',
  'properties': {
    'profiles': {'type': 'array', 'items': {'type': 'string'}},
  },
})
def api_hosts_hostname_patch(hostname):
  need_commit = False
  nodelist=nodeset(hostname)
  hosts = query_hosts(nodelist, check_count=True)
  profiles = []

  if 'profiles' in g.data:
    for p in g.data['profiles']:
      profiles.append(get_profile(p))

    for host in hosts:
      host.profiles = profiles

    need_commit = True

  if need_commit:
    db.session.commit()

  return jsonify(get_hosts_folded(nodelist))

@bp.route('/api/v1.0/hosts/<string:hostname>', methods=['GET'])
def api_hosts_hostname_get(hostname):
  return jsonify(get_hosts_folded(nodeset(hostname)))

@bp.route('/api/v1.0/profiles', methods=['POST'])
@expects_json({
  'type': 'object',
  'properties': {
    'name': {'type': 'string'},
    'attributes': {'type': 'object'},
    'weight': {'type': 'integer'},
  },
  'required': ['name']
})
def api_profiles_post():
  try:
    profile = Profile.from_dict(g.data)
    db.session.add(profile)
    db.session.commit()
  except SQLAlchemyError:
    json_abort(409, "Profile already exists")

  return jsonify(profile.to_dict())

@bp.route('/api/v1.0/profiles', methods=['GET'])
def api_profiles_get():
  profiles = db.session.query(Profile).all()
  r = []
  for p in profiles:
    r.append(p.to_dict())

  return jsonify(r)


@bp.route('/api/v1.0/profiles/<string:name>', methods=['DELETE'])
def api_profiles_profile_delete(name):
  delete_profile(name)
  db.session.commit()
  return make_response(jsonify({}), 204)


@bp.route('/api/v1.0/profiles/<string:name>', methods=['GET'])
def api_profiles_profile_get(name):
  profile = get_profile(name)
  return jsonify(profile.to_dict())

@bp.route('/api/v1.0/profiles/<string:name>', methods=['PATCH'])
@expects_json({
  'type': 'object',
  'properties': {
    'attributes': {'type': 'object'},
    'weight': {'type': 'integer'},
  },
})
def api_profiles_profile_patch(name):
  need_commit = False
  profile = get_profile(name)

  if 'attributes' in g.data:
    profile.attributes = g.data['attributes']
    need_commit = True

  if 'weight' in g.data:
    profile.weight = g.data['weight']
    need_commit = True

  if need_commit:
    db.session.commit()

  return make_response(jsonify(profile.to_dict()), 200)

@bp.route('/api/v1.0/resources', methods=['GET'])
def api_resources_get():
  resources = db.session.query(Resource).all()
  result = []
  for r in resources:
    result.append(r.to_dict())

  return jsonify(result)

@bp.route('/api/v1.0/resources', methods=['POST'])
@expects_json({
  'type': 'object',
  'properties': {
    'name': {'type': 'string'},
    'template_uri': {'type': 'string'},
  },
  'required': ['name', 'template_uri']
})
def api_resources_post():
  resource = Resource.from_dict(g.data)
  db.session.add(resource)
  db.session.commit()

  return jsonify(resource.to_dict())

@bp.route('/api/v1.0/resources/<string:name>', methods=['PATCH'])
@expects_json({
  'type': 'object',
  'properties': {
    'template_uri': {'type': 'string'},
  }
})
def api_resources_resource_patch():
  need_commit = False
  resource = get_resource(name)

  if 'attributes' in g.data:
    resource.template_uri = g.data['template_uri']
    need_commit = True

  if need_commit:
    db.session.commit()

  return make_response(jsonify(resource.to_dict()), 200)

@bp.route('/api/v1.0/resources/<string:name>', methods=['GET'])
def api_resources_resource_get():
  return jsonify(get_resource(name).to_dict())

@bp.route('/api/v1.0/resources/<string:name>', methods=['DELETE'])
def api_resources_resource_delete(name):
  resource = get_resource(name)
  db.session.delete(resource)
  db.session.commit()
  return make_response(jsonify({}), 204)

@bp.route('/api/v1.0/resources/<string:name>/<string:hostname>', methods=['GET'])
def api_resources_resource_render(name, hostname):
  a = get_alias(name, hostname, allow_fail=True)
  if not a:
    a = get_alias(name, allow_fail=True)

  if a:
    resource = a.target
  else:
    resource = get_resource(name)
    
  if a and a.autodelete:
    db.session.delete(a)
    db.session.commit()

  host = get_host(hostname)
  return make_response(render(resource.template_uri, host.attributes))

@bp.route('/api/v1.0/aliases', methods=['POST'])
@expects_json({
  'type': 'object',
  'properties': {
    'name': {'type': 'string'},
    'target': {'type': 'string'},
  },
  'additionalProperties': False,
  'required': ['name', 'target']
})
def api_aliases_post():
  exists = query_aliases(g.data['name'])
  if query_aliases(g.data['name']).count() > 0:
    json_abort(409, "Alias already exists")

  target = get_resource(g.data['target'])
  a = Alias(g.data['name'], target, None)

  db.session.add(a)
  db.session.commit()

  #TODO
  return jsonify({})

@bp.route('/api/v1.0/aliases/<string:name>', methods=['POST'])
@expects_json({
  'type': 'object',
  'properties': {
    'hosts': {'type': 'string'},
    'target': {'type': 'string'},
    'autodelete': {'type': 'boolean'},
  },
  'required': ['hosts', 'target']
})
def api_aliases_alias_post(name):
  exists = query_aliases(name)

  # Check if the main alias is defined
  main_alias = get_alias(name)

  if query_aliases(name, nodeset(g.data['hosts'])).count() > 0:
    json_abort(409, "Alias or override already exists")

  target = get_resource(g.data['target'])
  for i,host in enumerate(query_hosts(nodeset(g.data['hosts']),
                                      check_count=True).all()):
    a = Alias(name,
              target,
              host,
              g.data.get('autodelete', False))

    db.session.add(a)
    if i%1000 == 0:
      db.session.flush()

  db.session.commit()

  return jsonify({})

@bp.route('/api/v1.0/aliases/<string:name>', methods=['DELETE'])
def api_aliases_alias_delete(name):

  for a in query_aliases(name).all():
    db.session.delete(a)

  db.session.commit()
  return make_response(jsonify({}), 204)

@bp.route('/api/v1.0/aliases/<string:name>/<string:hostname>', methods=['DELETE'])
def api_aliases_alias_host_delete(name, hostname):

  for a in query_aliases(name, nodeset(hostname),
                         check_count=True).all():
    db.session.delete(a)

  db.session.commit()
  return make_response(jsonify({}), 204)

def alias_to_dict(name=None):
  r = {}
  for a in query_aliases(name).all():
    r.setdefault(a.name, {'name': a.name,
                          'overrides': {} })
    if a.host:
      r[a.name]['overrides'][a.host.hostname] = {'target': a.target.name,
                                                 'autodelete': a.autodelete}
    else:
      r[a.name]['target'] = a.target.name

  return r

@bp.route('/api/v1.0/aliases', methods=['GET'])
def api_aliases_get():
  r = alias_to_dict()
  return jsonify(r.values())

@bp.route('/api/v1.0/aliases/<string:name>', methods=['GET'])
def api_aliases_alias_get(name):
  return jsonify(alias_to_dict(name).values()[0])

@bp.route('/api/v1.0/aliases/<string:name>/<string:hostname>', methods=['GET'])
def api_aliases_alias_host_get(name):
  r = {}
  for a in query_aliases(name, nodeset(hostname), check_count=True).all():
    r[a.name][a.hostname] = {'target': a.target,
                             'autodelete': a.autodelete}
  return jsonify(r)








# @bp.route('/api/v1.0/scripts/<string:hostname>', methods=['GET'])
# def get_boot(hostname):
#   try:
#     h = get_host(hostname)
#     if h.target == 'deploy':
#       h.target = 'normal'
#       db.session.commit()
#       return make_response(render('deploy.jinja', h.profile.attributes))
#     else:
#       if h.target != 'normal':
#         h.target = 'normal'
#         db.session.commit()
#         return make_response(render("normal.jinja".format(h.target), h.profile.attributes))

#   except Exception as e:
#     return make_response(str(e))



# @bp.route('/api/v1.0/next_boot/<string:hostname>', methods=['GET','PUT'])
# def next_boot(hostname):
#   try:
#     h = get_host(hostname)
#     if request.method == 'PUT':
#       h.target = request.form['bootmethod']
#       db.session.commit()
#       return make_response('ok: next boot for {0} is {1} \n'.format(hostname,
#                                                                     h.target))
#     else:
#       return make_response('next boot is {0}\n'.format(h.target))
#   except Exception as e:
#     return make_response(str(e))


if __name__ == "__main__":
  if sys.argv[1] == 'initdb':
    init_db()
