import base64
from typing import Any

import yaml

from uaa_admin_config import (
    update_admin_client_secret,
    update_banner_background_color,
    update_banner_link,
    update_banner_logo,
    update_banner_text,
    update_banner_text_color,
    update_company_name,
    update_footer_legal_text,
    update_footer_links,
    update_product_logo,
    update_square_logo,
)


def setup_uaa_yml(tmp_path):
    """Helper function to create a dummy uaa.yml file."""
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
        },
        'login': {
            'branding': {}
        }
    }
    with open(uaa_yml_path, 'w') as f:
        yaml.dump(dummy_config, f)
    return uaa_yml_path


def test_update_admin_client_secret_success(tmp_path: Any):
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


def test_update_admin_client_secret_no_file(tmp_path: Any):
    """
    Test failure when uaa.yml does not exist.
    """
    result = update_admin_client_secret(str(tmp_path), "new_secret")
    assert result["status"] == "error"
    assert "not found" in result["message"]


def test_update_admin_client_secret_no_admin_client(tmp_path: Any):
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


def test_update_banner_logo(tmp_path: Any):
    uaa_yml_path = setup_uaa_yml(tmp_path)
    
    # Create a dummy png file
    dummy_png_path = tmp_path / "logo.png"
    # A 1x1 transparent PNG
    png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
    with open(dummy_png_path, "wb") as f:
        f.write(png_data)

    expected_base64 = base64.b64encode(png_data).decode('utf-8')

    result = update_banner_logo(str(tmp_path), str(dummy_png_path))
    assert result["status"] == "success"
    with open(uaa_yml_path) as f:
        config = yaml.safe_load(f)
    assert config['login']['branding']['banner']['logo'] == expected_base64


def test_update_banner_text(tmp_path: Any):
    uaa_yml_path = setup_uaa_yml(tmp_path)
    result = update_banner_text(str(tmp_path), "new_text")
    assert result["status"] == "success"
    with open(uaa_yml_path) as f:
        config = yaml.safe_load(f)
    assert config['login']['branding']['banner']['text'] == 'new_text'


def test_update_banner_text_color(tmp_path: Any):
    uaa_yml_path = setup_uaa_yml(tmp_path)
    result = update_banner_text_color(str(tmp_path), "#123456")
    assert result["status"] == "success"
    with open(uaa_yml_path) as f:
        config = yaml.safe_load(f)
    assert config['login']['branding']['banner']['textColor'] == '#123456'


def test_update_banner_background_color(tmp_path: Any):
    uaa_yml_path = setup_uaa_yml(tmp_path)
    result = update_banner_background_color(str(tmp_path), "#654321")
    assert result["status"] == "success"
    with open(uaa_yml_path) as f:
        config = yaml.safe_load(f)
    assert config['login']['branding']['banner']['backgroundColor'] == '#654321'


def test_update_banner_link(tmp_path: Any):
    uaa_yml_path = setup_uaa_yml(tmp_path)
    result = update_banner_link(str(tmp_path), "http://new.example.com")
    assert result["status"] == "success"
    with open(uaa_yml_path) as f:
        config = yaml.safe_load(f)
    assert config['login']['branding']['banner']['link'] == 'http://new.example.com'


def test_update_company_name(tmp_path: Any):
    uaa_yml_path = setup_uaa_yml(tmp_path)
    result = update_company_name(str(tmp_path), "New Company")
    assert result["status"] == "success"
    with open(uaa_yml_path) as f:
        config = yaml.safe_load(f)
    assert config['login']['branding']['companyName'] == 'New Company'


def test_update_product_logo(tmp_path: Any):
    uaa_yml_path = setup_uaa_yml(tmp_path)
    
    # Create a dummy png file
    dummy_png_path = tmp_path / "product_logo.png"
    # A 1x1 transparent PNG
    png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
    with open(dummy_png_path, "wb") as f:
        f.write(png_data)

    expected_base64 = base64.b64encode(png_data).decode('utf-8')

    result = update_product_logo(str(tmp_path), str(dummy_png_path))
    assert result["status"] == "success"
    with open(uaa_yml_path) as f:
        config = yaml.safe_load(f)
    assert config['login']['branding']['productLogo'] == expected_base64


def test_update_square_logo(tmp_path: Any):
    uaa_yml_path = setup_uaa_yml(tmp_path)
    
    # Create a dummy png file
    dummy_png_path = tmp_path / "square_logo.png"
    # A 1x1 transparent PNG
    png_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
    with open(dummy_png_path, "wb") as f:
        f.write(png_data)

    expected_base64 = base64.b64encode(png_data).decode('utf-8')

    result = update_square_logo(str(tmp_path), str(dummy_png_path))
    assert result["status"] == "success"
    with open(uaa_yml_path) as f:
        config = yaml.safe_load(f)
    assert config['login']['branding']['squareLogo'] == expected_base64


def test_update_footer_legal_text(tmp_path: Any):
    uaa_yml_path = setup_uaa_yml(tmp_path)
    result = update_footer_legal_text(str(tmp_path), "New Legal Text")
    assert result["status"] == "success"
    with open(uaa_yml_path) as f:
        config = yaml.safe_load(f)
    assert config['login']['branding']['footerLegalText'] == 'New Legal Text'


def test_update_footer_links(tmp_path: Any):
    uaa_yml_path = setup_uaa_yml(tmp_path)
    new_links = {"privacy": "http://privacy.com"}
    result = update_footer_links(str(tmp_path), new_links)
    assert result["status"] == "success"
    with open(uaa_yml_path) as f:
        config = yaml.safe_load(f)
    assert config['login']['branding']['footerLinks'] == new_links
