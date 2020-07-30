FROM centos
EXPOSE 5432

RUN curl -L -O  http://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
RUN rpm -ivh epel-release-latest-8.noarch.rpm

RUN yum -y --disableplugin=fastestmirror install python3-pip rpm-build mariadb-devel gcc python3-devel

WORKDIR bmgr

COPY . .

RUN pip3 install --upgrade setuptools pip

RUN pip3 install pytest

RUN pip3 install -r requirements.txt

RUN mkdir /etc/bmgr

RUN cp -r confs/templates /etc/bmgr/

ENV FLASK_APP=bmgr
ENV BMGR_CLIENT_URL=http://localhost:5000

CMD [ "flask", "run" ]

