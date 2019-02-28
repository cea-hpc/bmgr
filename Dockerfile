FROM centos
EXPOSE 5432

RUN curl -L -O  http://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
RUN rpm -ivh epel-release-latest-7.noarch.rpm

RUN yum -y --disableplugin=fastestmirror install python-pip MySQL-python
RUN yum -y --disableplugin=fastestmirror python-flask python-flask-sqlalchemy MySQL-python \
                                                  PyYAML clustershell python2-clustershell
RUN yum -y --disableplugin=fastestmirror install uwsgi uwsgi-plugin-python2

RUN yum -y --disableplugin=fastestmirror install rpm-build

WORKDIR bmgr

COPY . .

RUN pip install -r requirements.txt

RUN pip install pytest

RUN python setup.py bdist_rpm

CMD [ "uwsgi", "--master", "--socket","0.0.0.0:5432",  "--manage-script-name", "--protocol", "http", "--uid", "uwsgi", "--plugins", "python", "--mount", "/bmgr=bmgr:create_app()" ]
