import os
import tempfile
import pytest
import bmgr
import bmgr.server
import shutil

from ClusterShell.NodeSet import NodeSet as nodeset

@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    template_path = tempfile.mkdtemp()

    client_config = {
       'BMGR_DB_URI': 'sqlite:///{0}'.format(db_path),
       'TESTING': True,
       'BMGR_TEMPLATE_PATH': template_path
       #'SQLALCHEMY_ECHO': True
       }

    app = bmgr.create_app(client_config)
    client = app.test_client()

    app.testing = True
    with app.app_context():
        bmgr.server.init_db()

    with open(os.path.join(template_path, 'boot.jinja'), 'w+') as f:
        f.write('boot: a: {{ a }} b: {{ b }}')
    with open(os.path.join(template_path, 'deploy.jinja'), 'w+') as f:
        f.write('deploy: a: {{ a }} b: {{ b }}')

    yield client

    os.close(db_fd)
    os.unlink(db_path)
    shutil.rmtree(template_path)

def assert_empty_hosts(client):
    r = client.get('/api/v1.0/hosts')
    assert r.status_code == 200
    assert r.get_json() == []

def assert_empty_profiles(client):
    r = client.get('/api/v1.0/profiles')
    assert r.status_code == 200
    assert r.get_json() == []


def test_hosts(client):
    assert_empty_hosts(client)

    # Add hosts, one by one or with nodesets
    hosts_groups = 'cmp4329,svc256,node[1-50],node[51-998]'
    hosts_ns = nodeset(hosts_groups)

    hosts_to_create = hosts_groups.split(',')
    for hosts in hosts_to_create:
        r = client.post('/api/v1.0/hosts',
                        json = { 'name': hosts }
                        )
        assert r.status_code == 200
        assert r.get_json() == [{'name': hosts, 'profiles': [] }]

        # Try to re-add the same hosts and get a conflict
        r = client.post('/api/v1.0/hosts',
                        json = { 'name': hosts }
                        )
        assert r.status_code == 409

    # List hosts
    r = client.get('/api/v1.0/hosts')
    assert r.status_code == 200
    assert r.get_json() == [{ 'name': str(hosts_ns), 'profiles': [] }]

    # Get host
    r = client.get('/api/v1.0/hosts/node59')
    assert r.status_code == 200
    assert r.get_json() == [{ 'name': 'node59', 'profiles': [] }]


    # Delete non existing host
    r = client.delete('/api/v1.0/hosts/aaa')
    assert r.status_code == 404
    assert r.get_json() == {'error': 'Not found'}


    # Delete our hosts
    for host in str(hosts_ns).split(','):
        r = client.delete('/api/v1.0/hosts/{}'.format(host))
        assert r.status_code == 204

        # Delete a second time and get a not found error
        r = client.delete('/api/v1.0/hosts/{}'.format(host))
        assert r.status_code == 404
        assert r.get_json() == {'error': 'Not found'}

    assert_empty_hosts(client)

def test_profiles(client):
    assert_empty_profiles(client)

    profiles = [ {"name": "profileA",
                  "attributes": {"a1": "1", "a2": "2"}},
                 {"name": "profileB",
                  "attributes": {"b1": "1", "b2": "2"},
                  "weight": 10}]

    new_profiles = [ {"name": "profileA",
                      "attributes": {"a1": "1", "a3": "3"},
                      "weight": 10},
                     {"name": "profileB",
                      "attributes": {"b1": "1"}}]

    # Create some profiles
    for p in profiles:
        r = client.post('/api/v1.0/profiles',
                        json = p)


        assert r.status_code == 200

        expect = p
        expect.setdefault("weight", 0)
        assert r.get_json()  == expect

        # Create a second time and get a conflict
        r = client.post('/api/v1.0/profiles',
                        json = p)

        assert r.status_code == 409

    # Malformed request (no attributes)
    r = client.post('/api/v1.0/profiles',
                    json = {"name": "C"})
    assert r.status_code == 400

    # List profiles attributes
    for p in profiles:
        r = client.get('/api/v1.0/profiles/{}'.format(p['name']))
        assert r.status_code == 200

        expect = p
        expect.setdefault("weight", 0)
        assert r.get_json() == p

    # Update profiles attributes
    for p in new_profiles:
        r = client.patch('/api/v1.0/profiles/{}'.format(p['name']),
                         json = p)
        assert r.status_code == 200

        expect = p
        expect.setdefault("weight", 10)
        assert r.get_json() == p

    # List profiles attributes
    for p in new_profiles:
        r = client.get('/api/v1.0/profiles/{}'.format(p['name']))
        assert r.status_code == 200

        expect = p
        expect.setdefault("weight", 0)
        assert r.get_json() == p

    # Delete profiles
    for p in new_profiles:
        r = client.delete('/api/v1.0/profiles/{}'.format(p['name']))
        assert r.status_code == 204

        # Delete a second time and get a not found error
        r = client.delete('/api/v1.0/profiles/{}'.format(p))
        assert r.status_code == 404
        assert r.get_json() == {'error': 'Not found'}

def test_host_profiles(client):
    # Create some profiles
    profiles = [ {"name": "profileA",
                  "attributes": {"a": "1"}},
                 {"name": "profileB",
                  "attributes": {"b": "2"},
                  "weight": 10}]

    for p in profiles:
        r = client.post('/api/v1.0/profiles',
                        json = p)

        assert r.status_code == 200

    # Create hosts with non existing profiles
    r = client.post('/api/v1.0/hosts',
                    json = { 'name': 'node[0-9]' ,
                             'profiles': ['profileA', 'profileC']}
                    )
    assert r.status_code == 404
    assert_empty_hosts(client)

    # Create hosts with existing profiles
    r = client.post('/api/v1.0/hosts',
                    json = { 'name': 'node[0-9]' ,
                             'profiles': ['profileA']}
                    )
    assert r.status_code == 200

    # Check the profiles
    r = client.get('/api/v1.0/hosts/node[0-9]')
    assert r.status_code == 200
    assert r.get_json() == [{
        'name': 'node[0-9]',
        'profiles': ['profileA']}]

    # Update profiles for non existing host
    r = client.patch('/api/v1.0/hosts/node20',
                    json = {'profiles': ['profileA', 'profileB']})
    assert r.status_code == 404

    # Update profiles for part of the hosts
    r = client.patch('/api/v1.0/hosts/node[0-4]',
                    json = {'profiles': ['profileA', 'profileB']})
    assert r.status_code == 200

    assert r.get_json() == [{'name': 'node[0-4]',
                             'profiles': ['profileA', 'profileB']}]

    # Check new profiles
    r = client.get('/api/v1.0/hosts')
    assert r.status_code == 200
    assert sorted(r.get_json()) == sorted([{
            'name': 'node[0-4]',
            'profiles': ['profileA', 'profileB']
        },{
            'name': 'node[5-9]',
            'profiles': ['profileA']
        }])

    # Delete a profile
    r = client.delete('/api/v1.0/profiles/profileA')
    assert r.status_code == 204

    # Check new profiles
    r = client.get('/api/v1.0/hosts')
    assert r.status_code == 200
    assert sorted(r.get_json()) == sorted([{
            'name': 'node[0-4]',
            'profiles': ['profileB']
        },{
            'name': 'node[5-9]',
            'profiles': []
        }])

def test_resources(client):
    # Check default resources
    r = client.get('/api/v1.0/resources')
    assert r.status_code == 200
    assert len(r.get_json()) == 2
    for res in r.get_json():
        assert res['name'] in ('boot', 'deploy')

    # Add a resource
    resource_def = {'name': 'kickstart',
                    'template_uri': 'file://kstemplate.jinja'}

    r = client.post('/api/v1.0/resources',
                    json = resource_def)
    assert r.status_code == 200
    assert r.get_json() == resource_def

    # Check resources
    r = client.get('/api/v1.0/resources')
    assert r.status_code == 200
    assert len(r.get_json()) == 3
    for res in r.get_json():
        assert res['name'] in ('boot', 'deploy', 'kickstart')

    # Delete a resource
    r = client.delete('/api/v1.0/resources/kickstart')
    assert r.status_code == 204

    # Check resources
    r = client.get('/api/v1.0/resources')
    assert r.status_code == 200
    assert len(r.get_json()) == 2
    for res in r.get_json():
        assert res['name'] in ('boot', 'deploy')

    # Create some profiles
    profiles = [ {"name": "profileA",
                  "attributes": {"a": "1", "b": "1"},
                 "weight": 10},
                 {"name": "profileB",
                  "attributes": {"b": "2"}
                  }]

    for p in profiles:
        r = client.post('/api/v1.0/profiles',
                        json = p)

        assert r.status_code == 200

    # Create a host with a single profile
    r = client.post('/api/v1.0/hosts',
                    json = { 'name': 'node0' ,
                             'profiles': ['profileA']}
                    )
    assert r.status_code == 200

    # Render a resource
    r = client.get('/api/v1.0/resources/boot/node0')
    assert r.status_code == 200
    assert r.data == 'boot: a: 1 b: 1'

    # Add a second profile
    r = client.patch('/api/v1.0/hosts/node0',
                    json = {'profiles': ['profileA', 'profileB']})
    assert r.status_code == 200

    r = client.get('/api/v1.0/resources/boot/node0')
    assert r.status_code == 200
    assert r.data == 'boot: a: 1 b: 1'

    # Raise the priority of the second profile
    r = client.patch('/api/v1.0/profiles/profileB',
                    json = {'weight': 100})
    assert r.status_code == 200

    r = client.get('/api/v1.0/resources/boot/node0')
    assert r.status_code == 200
    assert r.data == 'boot: a: 1 b: 2'

def test_aliases(client):
    # Check default aliases
    r = client.get('/api/v1.0/aliases')
    assert r.status_code == 200
    assert r.get_json() == []

    # Create some test hosts
    r = client.post('/api/v1.0/hosts',
                    json = { 'name': 'node[0-10]' ,
                             'profiles': []}
                    )
    assert r.status_code == 200


    # Add bad aliases
    r = client.post('/api/v1.0/aliases',
                    json={'name': 'myalias',
                          'target': 'bad'})
    assert r.status_code == 404

    # Add correct alias
    r = client.post('/api/v1.0/aliases',
                    json={'name': 'myalias',
                          'target': 'boot'})
    assert r.status_code == 200

    # Override existing alias
    r = client.post('/api/v1.0/aliases/myalias',
                    json={'target': 'deploy',
                          'hosts': 'node[1-3]',
                          'autodelete': True})
    assert r.status_code == 200

    # Override existing alias with bad hosts
    r = client.post('/api/v1.0/aliases/myalias',
                    json={'target': 'deploy',
                          'hosts': 'node[12]',
                          'autodelete': True})
    assert r.status_code == 404

    # Override non-existing alias
    r = client.post('/api/v1.0/aliases/myalias2',
                    json={'target': 'deploy',
                          'hosts': 'node[6-9]',
                          'autodelete': True})
    assert r.status_code == 404

    # Get overriden alias
    r = client.get('/api/v1.0/aliases/myalias')
    assert r.status_code == 200
    assert r.get_json() == {'name': 'myalias',
                            'overrides':
                            {'node1': {'autodelete': True, 'target': 'deploy'},
                             'node2': {'autodelete': True, 'target': 'deploy'},
                             'node3': {'autodelete': True, 'target': 'deploy'}},
                             'target': 'boot'}

    # Add a second alias
    r = client.post('/api/v1.0/aliases',
                    json={'name': 'myalias2',
                          'target': 'deploy'})
    assert r.status_code == 200

    # Get all aliases
    r = client.get('/api/v1.0/aliases')
    assert r.status_code == 200
    print r.get_json()
    assert sorted(r.get_json()) == sorted(
        [{'name': 'myalias',
          'overrides':
          {'node1': {'autodelete': True, 'target': 'deploy'},
           'node2': {'autodelete': True, 'target': 'deploy'},
           'node3': {'autodelete': True, 'target': 'deploy'}},
          'target': 'boot'},
         {'name': 'myalias2',
          'target': 'deploy',
          'overrides': {}}])
    
    
    # Delete overriden alias
    r = client.delete('/api/v1.0/aliases/myalias/node1')
    assert r.status_code == 204

    r = client.get('/api/v1.0/aliases/myalias')
    assert r.status_code == 200
    assert r.get_json() == {'name': 'myalias',
                            'overrides':
                            {'node2': {'autodelete': True, 'target': 'deploy'},
                             'node3': {'autodelete': True, 'target': 'deploy'}},
                            'target': 'boot'}


    r = client.get('/api/v1.0/resources/deploy/node0')
    assert r.status_code == 200
    expect_deploy = r.data

    # Get reference resource rendering
    r = client.get('/api/v1.0/resources/boot/node0')
    assert r.status_code == 200
    expect_boot = r.data
    
    r = client.get('/api/v1.0/resources/myalias/node0')
    assert r.status_code == 200
    assert r.data == expect_boot

    # Test dynamic alias
    r = client.get('/api/v1.0/resources/myalias/node2')
    assert r.status_code == 200
    assert r.data == expect_deploy

    r = client.get('/api/v1.0/resources/myalias/node2')
    assert r.status_code == 200
    assert r.data == expect_boot

    # Test static alias
    r = client.post('/api/v1.0/aliases/myalias',
                    json={'target': 'deploy',
                          'hosts': 'node[2]',
                          'autodelete': False})
    assert r.status_code == 200

    r = client.get('/api/v1.0/resources/myalias/node2')
    assert r.status_code == 200
    assert r.data == expect_deploy

    r = client.get('/api/v1.0/resources/myalias/node2')
    assert r.status_code == 200
    assert r.data == expect_deploy

    # Delete overrides and aliases
    r = client.delete('/api/v1.0/aliases/myalias/node[2-3]')
    assert r.status_code == 204

    r = client.get('/api/v1.0/aliases/myalias')
    assert r.status_code == 200
    assert r.get_json() == {'name': 'myalias',
                            'target': 'boot',
                            'overrides': {}}


    r = client.delete('/api/v1.0/aliases/myalias')
    assert r.status_code == 204
    r = client.delete('/api/v1.0/aliases/myalias2')
    assert r.status_code == 204
    
