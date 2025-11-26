import yaml

from uaa_admin_config import update_admin_client_secret


def test_update_admin_client_secret_success(tmp_path):
    """
    Test successfully updating the admin client secret in a dummy uaa.yml.
    """
    scripts_boot_path = tmp_path / "scripts" / "boot"
    scripts_boot_path.mkdir(parents=True)
    uaa_yml_path = scripts_boot_path / "uaa.yml"

    dummy_config = {
        'oauth': {
            'clients': {
                'admin': {
                    'secret': 'old_secret'
                }
            }
        }
    }
    with open(uaa_yml_path, 'w') as f:
        yaml.dump(dummy_config, f)

    result = update_admin_client_secret(str(tmp_path), "new_secret")
    assert result["status"] == "success"

    with open(uaa_yml_path) as f:
        updated_config = yaml.safe_load(f)
    assert updated_config['oauth']['clients']['admin']['secret'] == 'new_secret'

def test_update_admin_client_secret_no_file(tmp_path):
    """
    Test failure when uaa.yml does not exist.
    """
    result = update_admin_client_secret(str(tmp_path), "new_secret")
    assert result["status"] == "error"
    assert "not found" in result["message"]

def test_update_admin_client_secret_no_admin_client(tmp_path):
    """
    Test failure when the 'admin' client is not in uaa.yml.
    """
    scripts_boot_path = tmp_path / "scripts" / "boot"
    scripts_boot_path.mkdir(parents=True)
    uaa_yml_path = scripts_boot_path / "uaa.yml"

    dummy_config = {
        'clients': {
            'other_client': {
                'secret': 'some_secret'
            }
        }
    }
    with open(uaa_yml_path, 'w') as f:
        yaml.dump(dummy_config, f)

    result = update_admin_client_secret(str(tmp_path), "new_secret")
    assert result["status"] == "error"
    assert "'admin' client not found" in result["message"]
