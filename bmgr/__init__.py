import os

from flask import Flask
from . import server

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # Outside of tests, conf is passed via a file, by default /etc/bmgr.conf
    # or the location specified in BMGR_CONF_FILE
    if test_config is None:
        app.config.from_envvar('BMGR_CONF_FILE', silent=True) or \
            app.config.from_pyfile('/etc/bmgr/bmgr.conf', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    db_uri = (os.environ.get('BMGR_DB_URI', None) or
              app.config.get('BMGR_DB_URI', None))

    # BUILD the database URI unless explicitely specified
    if db_uri:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
    else:
        try:
            app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{0}:{1}@{2}/bmgr'.format(
                os.environ.get('BMGR_DB_USER', None) or app.config['BMGR_DB_USER'],
                os.environ.get('BMGR_DB_PASS', None) or app.config['BMGR_DB_PASS'],
                os.environ.get('BMGR_DB_HOST', None) or app.config['BMGR_DB_HOST'])

        except KeyError:
            raise ValueError("Please provide a database host and user/password "
                             "or URI")

    app.config.setdefault('BMGR_TEMPLATE_PATH', '/etc/bmgr/templates/')
    app.config.setdefault('SQLALCHEMY_ENGINE_OPTIONS', {'pool_recycle' : 600})
    app.config.setdefault('SQLALCHEMY_TRACK_MODIFICATIONS', False)
    app.register_blueprint(server.bp)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Initialize the SQLAlchemy db object
    server.db.init_app(app)

    @app.cli.command(help='Intialize the bmgr database')
    def initdb():
        server.init_db()

    return app
