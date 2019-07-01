FROM centos
EXPOSE 5432

RUN curl -L -O  http://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
RUN rpm -ivh epel-release-latest-7.noarch.rpm

RUN yum -y --disableplugin=fastestmirror install python-pip MySQL-python \
                                         PyYAML clustershell python2-clustershell rpm-build

# RUN yum -y --disableplugin=fastestmirror install python-flask python-flask-sqlalchemy
#


WORKDIR bmgr

COPY . .

RUN pip install --upgrade setuptools

RUN pip install pytest==4.6.3

RUN pip install -r requirements.txt

# RUN python setup.py bdist_rpm

ENV FLASK_APP=bmgr
ENV BMGR_CLIENT_URL=http://localhost:5000

CMD [ "flask", "run" ]

