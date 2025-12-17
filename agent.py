"""Agent module for interacting with UAA and cloning repositories.

Refinements:
 - Environment-driven configuration for model and repo URL.
 - Retry logic for git clone with exponential backoff.
 - Logging configured only when executed as a script (not on import).
"""

# Standard library imports (alphabetized)
import logging
import os
import tempfile  # secure temporary directory creation

# Third-party imports
from google.adk.agents.llm_agent import Agent

# Local application imports
try:
    from .config import settings
except ImportError:
    from config import settings
try:
    from .uaa_server_clone import clone_repository
except ImportError:
    from uaa_server_clone import clone_repository
try:
    from .uaa_server_manager import (
        assemble_uaa,
        check_certificates_exist,
        clean_uaa,
        generate_certificate,
        get_java_version,
        get_java_version_from_sdkmanrc,
        run_uaa_detached,
        sdk_set_sdkmanrc_file,
        sdk_use_java_version,
        stop_uaa,
        wait_for_port,
    )
except ImportError:
    from uaa_server_manager import (
        assemble_uaa,
        check_certificates_exist,
        clean_uaa,
        generate_certificate,
        get_java_version,
        get_java_version_from_sdkmanrc,
        run_uaa_detached,
        sdk_set_sdkmanrc_file,
        sdk_use_java_version,
        stop_uaa,
        wait_for_port,
    )
try:
    from .uaa_server_information import UAAServerInformationClient
except ImportError:
    from uaa_server_information import UAAServerInformationClient
try:
    from .uaa_admin_config import (
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
except ImportError:
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
try:
    from .uaa_identity_zones import (
        UAAIdentityZonesClient,
        set_token_for_uaa_identity_zones_client,
    )
except ImportError:
    from uaa_identity_zones import (
        UAAIdentityZonesClient,
        set_token_for_uaa_identity_zones_client,
    )
try:
    from .uaa_token import UAAClientCredentialsGrantClient
except ImportError:
    from uaa_token import UAAClientCredentialsGrantClient
try:
    from .uaa_server_manager import (
        clean_uaa,
        get_java_version,
        get_java_version_from_sdkmanrc,
        sdk_set_sdkmanrc_file,
        sdk_use_java_version,
        stop_uaa,
        wait_for_port,
    )
except ImportError:
    from uaa_server_manager import (
        get_java_version,
        get_java_version_from_sdkmanrc,
        sdk_set_sdkmanrc_file,
        sdk_use_java_version,
        stop_uaa,
        wait_for_port,
    )


logger = logging.getLogger(__name__)
logging.basicConfig(
    level=settings.log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger.info('Logger initialized (script execution).')

# Goals
# 1. Get UAA server version
# 2. Install UAA server
# 3. Build UAA server
# 4. Run UAA server
# 5. Update UAA server with appropriate human approvals
# 6. Constantly look for changes in the UAA repo and pull them in automatically (use GitHub tools)
# 7. Inform client about new updates to the UAA server


# root_agent initialization will occur after function definitions to ensure names are defined.


def ask_human_approval(prompt: str = "Do you approve this action? (y/n): ") -> bool:
    """Prompt the user for human approval and return True if approved, False otherwise."""
    while True:
        response = input(prompt).strip().lower()
        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False
        else:
            print("Please enter 'y' or 'n'.")


# Now initialize root_agent after function definitions
uaa_server_information_client = UAAServerInformationClient(base_url=settings.uaa_base_url)
uaa_identity_zones_client = UAAIdentityZonesClient(base_url=settings.uaa_base_url)
uaa_client_credentials_grant_client = UAAClientCredentialsGrantClient(base_url=settings.uaa_base_url)
root_agent = Agent(
    model=settings.model,
    name='root_agent',
    description='Agent to manage users, user authentication and user authorization.',
    instruction='You are a helpful assistant that manages a UAA server and learns about users.',
    tools=[
        clone_repository,
        get_java_version,
        get_java_version_from_sdkmanrc,
        sdk_set_sdkmanrc_file,
        sdk_use_java_version,
        clean_uaa,
        update_admin_client_secret,
        # build_uaa,
        assemble_uaa,
        check_certificates_exist,
        generate_certificate,
        run_uaa_detached,
        wait_for_port,
        stop_uaa,
        # ask_human_approval,
        update_banner_logo,
        update_banner_text,
        update_banner_text_color,
        update_banner_background_color,
        update_banner_link,
        update_company_name,
        update_product_logo,
        update_square_logo,
        update_footer_legal_text,
        update_footer_links,
        uaa_server_information_client.get_server_information,
        uaa_server_information_client.get_openid_configuration,
        uaa_server_information_client.create_passcode,
        uaa_server_information_client.get_passcode,
        uaa_server_information_client.get_auto_login,
        uaa_server_information_client.create_auto_login,
        uaa_server_information_client.perform_login,
        set_token_for_uaa_identity_zones_client,
        uaa_identity_zones_client.create_an_identity_zone,
        uaa_identity_zones_client.get_identity_zone,
        uaa_identity_zones_client.get_all_identity_zones,
        uaa_client_credentials_grant_client.create_without_authorization,
    ],
)

# if __name__ == '__main__':
    # Configure logging only when running as a script to avoid overriding host application logging.
    # logging.basicConfig(
    #     level=settings.log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    # )
    # logger.info('Logger initialized (script execution).')
    # Only run the example clone when invoked directly.
    # _example_clone()

# Examples

def _example_clone(repo_url: str | None = None) -> None:
    """Example: clone UAA repo into an ephemeral temporary directory under /tmp.

    The directory is cleaned up automatically when the context exits.
    Repo URL can be overridden via env UAA_REPO_URL.
    """
    repo_url = repo_url or os.getenv('UAA_REPO_URL', 'https://github.com/cloudfoundry/uaa')
    with tempfile.TemporaryDirectory(prefix='uaa_repo_', dir='/tmp') as tmpdir:
        logger.info("Cloning repository '%s' into temporary dir: %s", repo_url, tmpdir)
        success = clone_repository(repo_url, tmpdir)
        if success:
            try:
                logger.info('Clone completed. Contents: %s', os.listdir(tmpdir))
            except Exception:
                logger.debug('Could not list contents of %s', tmpdir)
        else:
            logger.warning('Clone failed; temporary directory will still be cleaned up.')