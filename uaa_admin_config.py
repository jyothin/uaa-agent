import os
import yaml
import logging

logger = logging.getLogger(__name__)

def update_admin_client_secret(destination_path: str, client_secret: str):
    """
    Updates the client_secret for the 'admin' client ID in the uaa.yml file.
    Ensure all sensitive data is masked in logs and outputs.
    """
    if not os.path.exists(destination_path):
        return {"status": "error", "message": f"{destination_path} not found"}

    uaa_yml_path = os.path.join(destination_path, 'scripts', 'boot', 'uaa.yml')

    if not os.path.exists(uaa_yml_path):
        return {"status": "error", "message": f"uaa.yml not found at {uaa_yml_path}"}

    try:
        with open(uaa_yml_path) as f:
            uaa_config = yaml.safe_load(f)

        if 'oauth' in uaa_config and 'clients' in uaa_config['oauth'] and 'admin' in uaa_config['oauth']['clients']:
            uaa_config['oauth']['clients']['admin']['secret'] = client_secret
        else:
            return {"status": "error", "message": "'admin' client not found in uaa.yml"}

        with open(uaa_yml_path, 'w') as f:
            yaml.dump(uaa_config, f)

        return {"status": "success", "message": "Admin client secret updated successfully."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to update uaa.yml: {e}"}
