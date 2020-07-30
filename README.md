# bmgr (Boot Manager)

bmgr is intended to generate and serve configuration files or scripts
used in the boot and deployment sequence of a server, such as
Kickstart, iPXE or Cloud-init files. It can be seen as a subset of
Cobbler focused on boot script generation. It is implemented as a
small piece of python code providing a Flask-based HTTP backend and
the related client. Its interface is based on nodesets which helps to
manage large scale clusters.

Boot scripts are identified as *resources* within bmgr and are
generated from Jinja templates. These templates are rendered
dynamically each time a *host* requests a resource, according to the
attributes that have been associated to the host.

To associate attributes to a host, you first have to define *profiles*
which hold a collection of attributes and are given a weight. You can
then associate hosts to one ore more profiles. If an attribute is
defined multiple times, the value of the attribute in the heaviest
profile is used.

It is also possible to define resource *aliases* which allow a resource
to point to one template or the other depending on the situation.

A typical usage is to switch between a normal boot from the server
disk and a deployment boot to reinstall the server from the
network. To achieve this, you can create a 'boot' alias that points to
the 'normal' resource by default and make that alias point to the
'deploy' resource when you want to redeploy your server. You can make
that alias 'oneshot' so that the 'deploy' resource is only served once
while subsequent requests return the 'normal' resource.


## Quick evaluation of bmgr using Docker

1. Deploy a http server and database with docker-compose

From the repository root:

```bash
# docker-compose up -d
```

2. Join the bmgr container

```bash
# docker exec -ti bmgr_bmgr_1 /bin/bash
```

3. Initialize the datbase
```bash
# FLASK_APP=bmgr.app flask initdb
```

4. Try the CLI (see more CLI usage examples below)

```bash
$ bmgr resource list
```

5. Edit resource templates to your needs in `/etc/bmgr/templates`

## Installation (Apache WSGI + MySQL backend)

1. Install the RPM

```bash
# yum install bmgr
```

2. Choose and configure database credentials

```bash
# mysql
  > CREATE DATABASE bmgr;
  > CREATE USER 'bmgr_user' IDENTIFIED BY 'bmgr_pass';
  > GRANT ALL PRIVILEGES ON bmgr.* TO bmgr_user@'%';
  > FLUSH PRIVILEGES;
```

3. Initialize the database

```bash
# FLASK_APP=bmgr.app flask initdb
```

4. Configure apache

```bash
# echo 'WSGIScriptAlias /bmgr "/var/www/bmgr/bmgr.wsgi"' >> /etc/httpd/conf/httpd.conf
# systemctl restart httpd
```


## bmgr client usage examples
### Hosts
- List hosts: `bmgr host list`
- Add hosts: `bmgr host add --profiles PROFILES HOSTS`
- Update hosts: `bmgr host update --profiles PROFILES HOSTS`
- Delete hosts: `bmgr host del HOSTS`
- Show hosts: `bmgr host show HOSTS`

### Profiles
- List profiles: `bmgr profile list`
- Add profile: `bmgr profile add PROFILE --attr ATTR1 VAL1 --attr ATTR2 VAL2 --weight WEIGHT`
- Update profile: `bmgr profile update PROFILE --attr ATTR1 VAL1 --attr ATTR2 VAL2 --del-attr ATTR3 --weight WEIGHT`
- Show profile: ` bmgr profile show PROFILE`

### Resources
- List resources: `bmgr resource list`
- Add resource: `bmgr resource add RESOURCE TEMPLATE`
- Delete resource: `bmgr resource del RESOURCE`
- Update resource: `bmgr resource update RESOURCE --template TEMPLATE`
- Render resource: `bmgr resource render RESOURCE HOSTNAME`

### Aliases
- List aliases: `bmgr alias list`
- Add alias: `bmgr alias add ALIAS TARGET`
- Delete alias: `bmgr alias add ALIAS`
- Override alias: `bmgr alias override (--oneshot) ALIAS HOSTNAMES TARGET`
- Restore alias: `bmgr alias restore ALIAS HOSTNAMES`

## REST API Endpoints

### Hosts
- [Show hosts](docs/hosts.md#list-hosts): `GET /api/v1.0/hosts`
- [Get host](docs/hosts.md#get-host): `GET /api/v1.0/hosts/:hostname`
- [Delete host](docs/hosts.md#delete-host): `DELETE /api/v1.0/hosts/:hostname`
- [Add hosts](docs/hosts.md#add-host): `POST /api/v1.0/hosts`
- [Update host](docs/hosts.md#update-host): `PATCH /api/v1.0/hosts/:hostname`

### Profiles
- [Show profiles](docs/profiles.md#list-profiles): `GET /api/v1.0/profiles`
- [Show profile](docs/profiles.md#get-profile): `GET /api/v1.0/profiles/:profile`
- [Delete profile](docs/profiles.md#delete-profile): `DELETE /api/v1.0/profiles/:profile`
- [Add profiles](docs/profiles.md#add-profiles): `POST /api/v1.0/profiles`
- [Update profile](docs/profiles.md#update-profiles): `PATCH /api/v1.0/profiles/:profile`

### Resources (templates)
- [Show resources](docs/resources.md#list-resources): `GET /api/v1.0/resources`
- [Get resource](docs/resources.md#get-resource): `GET /api/v1.0/resources/:resource`
- [Add resources](docs/resources.md#add-resources): `POST /api/v1.0/resources`
- [Delete resource](docs/resources.md#delete-resource): `DELETE /api/v1.0/resources/:resource`
- [Update resource](docs/resources.md#update-resources): `PATCH /api/v1.0/resources/:resource`
- [Render resource](docs/resources.md#render-resource): `GET /api/v1.0/resources/:resource/:hostname`

### Aliases
- [Show aliases](docs/aliases.md#list-aliases): `GET /api/v1.0/aliases`
- [Show alias](docs/aliases.md#get-alias): `GET /api/v1.0/aliases/:alias`
- [Add aliases](docs/aliases.md#add-alias): `POST /api/v1.0/aliases`
- [Add alias override](docs/aliases.md#add-alias-override): `POST /api/v1.0/aliases/:alias`
- [Delete global alias](docs/aliases.md#delete-alias): `DELETE /api/v1.0/aliases/:alias`
- [Delete host-alias](docs/aliases.md#delete-alias-override): `DELETE /api/v1.0/aliases/:alias/:hostname`
