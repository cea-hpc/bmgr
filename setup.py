#!/usr/bin/env python
import os
import glob
from setuptools.command.bdist_rpm import bdist_rpm
from setuptools.command.install import install
from setuptools import setup, find_packages


class bmgr_bdist_rpm(bdist_rpm):
    user_options = bdist_rpm.user_options + [
        ('macros=', None, 'Specfiy macros in RPM header')]

    def initialize_options(self):
        bdist_rpm.initialize_options(self)
        self.macros = None

    def _make_spec_file(self):
        spec = bdist_rpm._make_spec_file(self)
        if self.macros:
            spec = [ l.strip() for l in open(self.macros).readlines() ] + spec
        return spec

class bmgr_install(install):
    user_options = install.user_options + [
        ('unitdir=', None, 'Specfiy folder to install systemd units'),
        ('mandir=', None, 'Specfiy folder to install man pages'),
        ('sysconfdir=', None, 'Specfiy folder to install configuration files'),
        ('pkgdocdir=', None, 'Specfiy folder to install documentation files')]

    def initialize_options(self):
        self.unitdir = None
        self.mandir='share/man'
        self.pkgdocdir='share/doc/bmgr'
        self.sysconfdir='/etc'
        self.webdir='/var/www'
        install.initialize_options(self)

    def finalize_options(self):
        self.distribution.data_files.append((os.path.join(self.sysconfdir, 'bmgr'),
                                             ['confs/bmgr.conf']))
        self.distribution.data_files.append((os.path.join(self.sysconfdir, 'bmgr/templates'),
                                             ['confs/templates/normal.jinja',
                                              'confs/templates/deploy.jinja']))
        self.distribution.data_files.append((self.pkgdocdir,
                                             ['README']))
        self.distribution.data_files.append((os.path.join(self.webdir, 'bmgr'),
                                             ['confs/bmgr.wsgi']))
        install.finalize_options(self)

setup(name= 'bmgr', version= '0.2', description= 'Simple iPXE boot manager',
      long_description= 'Simple tool to manage PXE boot requests with a RESTful'
      ' interface',
      author= 'Francois Diakhate', author_email= 'francois.diakhate@cea.fr',
      license= "GPLv3", package_dir={'bmgr': 'bmgr', 'bmgr.scripts': 'bmgr/scripts'},
      packages=['bmgr','bmgr.scripts'],
      data_files=[],
      entry_points= '''
        [console_scripts]
        bmgr=bmgr.scripts.cmd:cli
      ''',
      install_requires=['Flask', 'flask', 'Flask-SQLAlchemy',
                        'MySQL-python','ClusterShell',
                        'flask-expects-json', 'requests', 'click',
                        'texttable'],
      cmdclass={'bdist_rpm': bmgr_bdist_rpm,
                'install': bmgr_install}
)
