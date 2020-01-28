import requests

class Client(object):
    def __init__(self, base_url):
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        self._base_url = base_url
        self._s = requests.Session()

    def _url(self, view, res=None, subres=None):
        view_url = '{}/api/v1.0/{}'.format(self._base_url, view)

        if res:
            view_url = '{}/{}'.format(view_url, res)
        else:
            return view_url

        if subres:
            return '{}/{}'.format(view_url, subres)
        else:
            return view_url


    def _validate_resp(self, r):
        r.raise_for_status()

        if r.text:
            return r.json()
        else:
            return None

    def _hosts_req(self, nodeset, profiles):
        json = {'name': str(nodeset)}
        if profiles:
            json['profiles'] = profiles

        return json

    def _resource_req(self, resource, template):
        json = {'name': resource}
        if template:
            json['template_uri'] = template

        return json


    def _alias_req(self, alias, target):
        json = {'name': alias}
        if target:
            json['target'] = target

        return json

    def _override_req(self, nodeset, target, oneshot):
        json = {'hosts': str(nodeset)}
        if target:
            json['target'] = target

        if oneshot:
            json['autodelete'] = True

        return json


    def _profile_req(self, profile, attrs, weight):
        json = {'name': profile}

        if attrs is not None:
            json['attributes'] = dict(attrs)

        if weight is not None:
            json['weight'] = weight

        return json

    def get_hosts(self, hosts=None):
        r = self._s.get(self._url('hosts', hosts))
        return self._validate_resp(r)

    def add_hosts(self, nodeset, profiles):
        r = self._s.post(
            self._url('hosts'),
            json = self._hosts_req(nodeset, profiles)
        )
        return self._validate_resp(r)

    def update_hosts(self, nodeset, profiles):
        r = self._s.patch(
            self._url('hosts', str(nodeset)),
            json = {'profiles': profiles}
        )
        return self._validate_resp(r)

    def del_hosts(self, nodeset):
        r = self._s.delete(
            self._url('hosts', str(nodeset))
        )
        return self._validate_resp(r)

    def get_profiles(self):
        r = self._s.get(self._url('profiles'))
        return self._validate_resp(r)

    def add_profile(self, profile, attrs=None, weight=None):
        r = self._s.post(
            self._url('profiles'),
            json = self._profile_req(profile, attrs, weight)
        )
        return self._validate_resp(r)

    def get_profile(self, profile):
        r = self._s.get(
            self._url('profiles', profile),
        )

        return self._validate_resp(r)

    def del_profile(self, profile):
        r = self._s.delete(
            self._url('profiles', profile)
        )
        return self._validate_resp(r)

    def update_profile(self, profile, attrs=None, weight=None):
        if attrs:
            cur_profile = self._s.get(
                self._url('profiles', profile),
            )
            cur_profile = self._validate_resp(cur_profile)

            new_attrs = cur_profile['attributes']

            for k, v in attrs:
                if v is None:
                    del new_attrs[k]
                else:
                    new_attrs[k] = v

            attrs = new_attrs

        r = self._s.patch(
            self._url('profiles', profile),
            json = self._profile_req(profile, attrs, weight)
        )
        return self._validate_resp(r)

    def add_resource(self, resource, template):
        r = self._s.post(
            self._url('resources'),
            json = self._resource_req(resource, template)
        )
        return self._validate_resp(r)

    def get_resources(self, resource=None):
        r = self._s.get(
            self._url('resources', resource),
        )

        return self._validate_resp(r)

    def del_resource(self, resource):
        r = self._s.delete(
            self._url('resources', resource)
        )
        return self._validate_resp(r)

    def update_resource(self, resource, template):
        r = self._s.patch(
            self._url('resources', resource),
            json = self._resource_req(resource, template)
        )
        return self._validate_resp(r)


    def render_resource(self, resource, host):
        r = self._s.get(
            self._url('resources', resource, host)
        )

        r.raise_for_status()
        return r.text

    def get_aliases(self, alias=None):
        r = self._s.get(
            self._url('aliases', alias),
        )

        return self._validate_resp(r)

    def add_alias(self, alias, target):
        r = self._s.post(
            self._url('aliases'),
            json = self._alias_req(alias, target)
        )
        return self._validate_resp(r)

    def del_alias(self, alias):
        r = self._s.delete(
            self._url('aliases', alias),
        )
        return self._validate_resp(r)

    def add_override(self, alias,  hosts, target, oneshot):
        r = self._s.post(
            self._url('aliases', alias),
            json = self._override_req(hosts, target, oneshot)
        )

        return self._validate_resp(r)

    def restore_alias(self, alias, hosts):
        r = self._s.delete(
            self._url('aliases', alias, hosts)
        )
        return self._validate_resp(r)



