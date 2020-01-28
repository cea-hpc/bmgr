import pytest
import responses
import requests
import os
from bmgr.scripts.cmd import cli
from click.testing import CliRunner

@pytest.fixture
def runner():
    return CliRunner()


os.environ['BMGR_CLIENT_URL'] = "http://testapi.com/"

@responses.activate
def test_hosts_list_cli(runner):
    responses.add(responses.GET, 'http://testapi.com/api/v1.0/hosts',
                  json=[{'name': 'node[0-9]' ,
                        'profiles': ['profileA', 'profileC']}], status=200)

    result = runner.invoke(cli, ['host', 'list'])
    assert "profileA,profileC   node[0-9]" in result.output
    assert result.exit_code == 0

@responses.activate
def test_hosts_list_cli_bad(runner):
    responses.add(responses.GET, 'http://testapi.com/api/v1.0/hosts',
                  json={'error': 'test error'}, status=500)

    result = runner.invoke(cli, ['host', 'list'])
    assert 'test error' in result.output
    assert result.exit_code != 0


@responses.activate
def test_profiles_list_cli(runner):
    responses.add(responses.GET, 'http://testapi.com/api/v1.0/profiles',
                  json=[{"name": "profileA",
                         "attributes": {"a1": "1", "a2": "2"},
                         "weight": 5},
                        {"name": "profileB",
                         "attributes": {"b1": "1", "b2": "2"},
                         "weight": 10}],
                  status=200)

    result = runner.invoke(cli, ['profile', 'list'])
    assert "profileA" in result.output
    assert "profileB" in result.output
    assert "a1" in result.output
    assert "a2" in result.output
    assert result.exit_code == 0
