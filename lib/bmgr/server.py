#!/bin/python
from flask import Flask, jsonify, make_response, abort, request
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, synonym
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import Column, Integer, String, ForeignKey
import subprocess, tempfile, os, stat, flask, json, jinja2
import ClusterShell.NodeSet

# grant all privileges on bmgr.* to bmgr_user@'%[hostname]' identified by 'XXXX'

basedir = os.path.abspath(os.path.dirname(__file__))


app = Flask(__name__)


exec(open("/etc/bmgr.conf").read())

SQLALCHEMY_DATABASE_URI = 'mysql://{0}:{1}@{2}/bmgr'.format(DB_USER, DB_PASS, DB_HOST)
engine = create_engine(SQLALCHEMY_DATABASE_URI, convert_unicode=True, echo=True, pool_recycle=600)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=True,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True)
    _attributes = Column('attributes', String(8000))
    hosts = relationship("Host", back_populates="profile",
                           uselist=True)

    @property
    def attributes(self):
        return json.loads(self._attributes)

    @attributes.setter
    def attributes(self, value):
        self._attributes = json.dumps(value)

    attributes = synonym('_attributes', descriptor=attributes)

    def __init__(self, name, attributes={}):
        self.name = name
        self.attributes = json.dumps(attributes)

    def __repr__(self):
        return '<Profile %r>' % (self.name)

class Host(Base):
    __tablename__ = 'hosts'
    id = Column(Integer, primary_key=True)
    hostname = Column(String(255), unique=True)
    target = Column(String(120))
    profile_id = Column(Integer, ForeignKey('profiles.id'))
    profile = relationship("Profile", back_populates="hosts",
                           uselist=False)

    def __init__(self, hostname, target='normal'):
        self.hostname = hostname
        self.target = target

    def __repr__(self):
        return '<Host %r>' % (self.hostname)


def init_db():
    Base.metadata.create_all(bind=engine)
    d = Profile('default')
    db_session.add(d)
    db_session.commit()

def get_host(hostname):
    try:
        h = db_session.query(Host).filter_by(hostname=hostname).one()
    except NoResultFound:
        h = Host(hostname)
        h.profile = db_session.query(Profile).filter_by(name='default').one()
        db_session.add(h)
        db_session.commit()

    return h


def get_profile(profile_name):
    try:
        p = db_session.query(Profile).filter_by(name=profile_name).one()
    except NoResultFound:
        p = Profile(profile_name)
        db_session.add(p)
        db_session.commit()

    return p

def render(tpl, context):
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader('/var/www/bmgr')
    ).get_template(tpl).render(context)

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

@app.route('/api/v1.0/scripts/<string:hostname>', methods=['GET'])
def get_boot(hostname):
    try:
        h = get_host(hostname)
        if h.target == 'deploy':
            h.target = 'normal'
            db_session.commit()
            return make_response(render('deploy.jinja', h.profile.attributes))
        else:
            if h.target != 'normal':
                h.target = 'normal'
                db_session.commit()
            return make_response(render("normal.jinja".format(h.target), h.profile.attributes))

    except Exception as e:
        return make_response(str(e))


@app.route('/api/v1.0/host_profile/<string:hostname>', methods=['GET', 'PUT'])
def host_profile(hostname):
    try:
        h = get_host(hostname)
        if request.method == 'PUT':
            profile_name = request.form['profile']
            p = db_session.query(Profile).filter_by(name=profile_name).one()
            h.profile = p
            db_session.commit()
            return make_response('ok\n')
        else:
            s = 'profile: {0}\n'.format(h.profile.name)
            try:
                for attr, val in h.profile.attributes.iteritems():
                    s+= '{0}: {1}\n'.format(attr, val)
            except:
                pass
            return make_response(s)

    except Exception as e:
        return make_response(str(e))


@app.route('/api/v1.0/profile', methods=['GET'])
def list_profile():
    try:
        profiles = db_session.query(Profile).all()
        s = ''.join(['{0}: {1}\n'.format(p.name, str(ClusterShell.NodeSet.fold(','.join([h.hostname
                                                                                         for h in p.hosts])))) for p in profiles if p.hosts])
        return make_response(s)
    except Exception as e:
        return make_response(str(e))

@app.route('/api/v1.0/profile/<string:profile_name>', methods=['GET', 'PUT'])
def profile(profile_name):
    try:
        if request.method == 'PUT':
            p = get_profile(profile_name)

            attrs = p.attributes
            if not isinstance(attrs, dict):
                attrs = {}

            for attr, value in request.form.iteritems():
                attrs[attr] = value

            p.attributes = attrs

            db_session.commit()
            return make_response('ok\n')
        else:
            p = get_profile(profile_name)
            return make_response(''.join(['{0}: {1}\n'.format(attr, val) for attr, val in p.attributes.iteritems()]))
    except Exception as e:
        return make_response(str(e))

@app.route('/api/v1.0/next_boot/<string:hostname>', methods=['GET','PUT'])
def next_boot(hostname):
    try:
        h = get_host(hostname)
        if request.method == 'PUT':
            h.target = request.form['bootmethod']
            db_session.commit()
            return make_response('ok: next boot for {0} is {1} \n'.format(hostname, h.target))
        else:
            return make_response('next boot is {0}\n'.format(h.target))
    except Exception as e:
        return make_response(str(e))
