FROM centos
EXPOSE 5432

RUN curl -L -O  http://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
RUN rpm -ivh epel-release-latest-7.noarch.rpm

RUN yum -y --disableplugin=fastestmirror install python-pip python-flask python-flask-sqlalchemy MySQL-python \
                                                 PyYAML clustershell python2-clustershell
RUN yum -y --disableplugin=fastestmirror install uwsgi uwsgi-plugin-python2

RUN yum -y --disableplugin=fastestmirror install rpm-build

COPY . .

RUN pip install -r requirements.txt

RUN python setup.py bdist_rpm

CMD [ "uwsgi", "--master", \
               "--socket", "0.0.0.0:5432", \
               "--uid", "uwsgi", \
               "--plugins", "python", \
               "--protocol", "http", \
	       "--manage-script-name", \
               "--mount", "/bmgr=bmgr.server:app" ]