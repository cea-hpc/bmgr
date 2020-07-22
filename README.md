# bmgr (Boot Manager)

bmgr is a small piece of python code that includes a Flask-based HTTP backend and the related python client.
It is intented to be used as a Kickstart/iPXE/Cloud-init script generator by using hierachical profile assigned
to configured nodes.

You can see this as a condensed version of cobbler, where only the script generator is present.

bmgr work by assigning hosts (identified by their hostnames) to multiple profiles.
Each profile got a weight and arbitrary attributes.
If an attribute exists in multiple profiles, the value of the attribute in the heaviest profile if used.

Scripts are generated using Jinja templates, identified as *resources* within bmgr.
Resources as rendered per-host and uses the attributes available in host's profiles.

An additional concept of alias is also present in bmgr. A bmgr alias is simply a resource alias that can change automatically.
You can define per-host 'oneshot' aliases that can route requests to a different template only once.
A typical usage is for deploy-mode vs. normal-boot mode :
- Add a 'boot' alias that points to the 'normal' resource by default
- Add a second 'boot' ontshot alias for a single host that points to the 'deploy' resource.
- As soon as the resource is rendered through the oneshot alias, the alias is deleted. ie. When the node is deployed, boot mode switch back to 'normal' mode.


## Installation (Apache WSGI + MySQL backend)

1. Install the RPM

```bash
# yum install bmgr
```

1. Choose and configure database credentials

```bash
# mysql
  > CREATE DATABASE bmgr;
  > CREATE USER 'bmgr_user' IDENTIFIED BY 'bmgr_pass';
  > GRANT ALL PRIVILEGES ON bmgr.* TO bmgr_user@'%';
  > FLUSH PRIVILEGES;
```

1. Initialze the database

```bash
# FLASK_APP=bmgr.app flask initdb
```

1. Configure apache

```bash
# echo 'WSGIScriptAlias /bmgr "/var/www/bmgr/bmgr.wsgi"' >> /etc/httpd/conf/httpd.conf
# systemctl restart httpd
```

1. Try it out

```bash
$ bmgr resource list
```

1. Edit resource template to your needs in `/etc/bmgr/templates`

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
