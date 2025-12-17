"""UAA admin and branding configuration editors.

Edits `scripts/boot/uaa.yml` to:
- update the 'admin' client secret
- modify `login.branding` (logos, text, colors, links, company/product names, footer text/links)

All helpers avoid logging sensitive values and return structured results.
"""

import base64
import logging
import os

import yaml

logger = logging.getLogger(__name__)

def update_admin_client_secret(destination_path: str, client_secret: str):
    """
    Updates the client_secret for the 'admin' client ID in the uaa.yml file.
    Ensure all sensitive data is masked in logs and outputs.
    DO NOT echo any client secrets in the repsonses or logs.
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

# login:
#   branding:
#     banner:
#       logo: iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAATBJREFUeNqk008og3Ecx/HNnrJSu63kIC5qKRe7KeUiOSulTHJUTrsr0y5ycFaEgyQXElvt5KDYwU0uO2hSUy4KoR7v7/qsfmjPHvzq1e/XU8/39/3zPFHf9yP/WV7jED24nGRbxDFWUAsToM05zyKFLG60d/wmQBxWzwyOlMU1phELEyCmtPeRQRoVbKOM0VYB6q0QW+3IYQpJFFDEYFCAiMqwNY857Ko3SxjGBTbRXb+xMUamcMbWh148YwJvOHSCdyqTAdxZo72ADGwKT98C9CChcxUPQSVYLz50toae4Fy9WcAISl7AiN/RhS1N5RV5rOLxx5eom90pvGAI/VjHMm6bfspK18a1gXvsqM41XDVL052C1Tim56cYd/rR+mdSrXGluxfm5S8Z/HV9CjAAvQZLXoa5mpgAAAAASUVORK5CYII=
#       text: cool beagle
#       textColor: "#F23456"
#       backgroundColor: "#F99999"
#       link: http://example.com
#     companyName: company name
#     productLogo: iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAATBJREFUeNqk008og3Ecx/HNnrJSu63kIC5qKRe7KeUiOSulTHJUTrsr0y5ycFaEgyQXElvt5KDYwU0uO2hSUy4KoR7v7/qsfmjPHvzq1e/XU8/39/3zPFHf9yP/WV7jED24nGRbxDFWUAsToM05zyKFLG60d/wmQBxWzwyOlMU1phELEyCmtPeRQRoVbKOM0VYB6q0QW+3IYQpJFFDEYFCAiMqwNY857Ko3SxjGBTbRXb+xMUamcMbWh148YwJvOHSCdyqTAdxZo72ADGwKT98C9CChcxUPQSVYLz50toae4Fy9WcAISl7AiN/RhS1N5RV5rOLxx5eom90pvGAI/VjHMm6bfspK18a1gXvsqM41XDVL052C1Tim56cYd/rR+mdSrXGluxfm5S8Z/HV9CjAAvQZLXoa5mpgAAAAASUVORK5CYII=
#     squareLogo: iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAAGXRFWHRTb2Z0d2FyZQBBZG9iZSBJbWFnZVJlYWR5ccllPAAAATBJREFUeNqk008og3Ecx/HNnrJSu63kIC5qKRe7KeUiOSulTHJUTrsr0y5ycFaEgyQXElvt5KDYwU0uO2hSUy4KoR7v7/qsfmjPHvzq1e/XU8/39/3zPFHf9yP/WV7jED24nGRbxDFWUAsToM05zyKFLG60d/wmQBxWzwyOlMU1phELEyCmtPeRQRoVbKOM0VYB6q0QW+3IYQpJFFDEYFCAiMqwNY857Ko3SxjGBTbRXb+xMUamcMbWh148YwJvOHSCdyqTAdxZo72ADGwKT98C9CChcxUPQSVYLz50toae4Fy9WcAISl7AiN/RhS1N5RV5rOLxx5eom90pvGAI/VjHMm6bfspK18a1gXvsqM41XDVL052C1Tim56cYd/rR+mdSrXGluxfm5S8Z/HV9CjAAvQZLXoa5mpgAAAAASUVORK5CYII=
#     footerLegalText: Legal text
#     footerLinks:
#       terms of service: http://terms.of.service/

def _update_branding_value(destination_path: str, key_path: list[str], value):
    """
    Generic function to update a value in the uaa.yml file under login.branding.
    """
    if not os.path.exists(destination_path):
        return {"status": "error", "message": f"{destination_path} not found"}

    uaa_yml_path = os.path.join(destination_path, 'scripts', 'boot', 'uaa.yml')

    if not os.path.exists(uaa_yml_path):
        return {"status": "error", "message": f"uaa.yml not found at {uaa_yml_path}"}

    try:
        with open(uaa_yml_path) as f:
            uaa_config = yaml.safe_load(f)

        # Navigate to the correct dictionary
        current_level = uaa_config.setdefault('login', {}).setdefault('branding', {})
        for key in key_path[:-1]:
            current_level = current_level.setdefault(key, {})
        
        current_level[key_path[-1]] = value

        with open(uaa_yml_path, 'w') as f:
            yaml.dump(uaa_config, f)

        return {"status": "success", "message": f"{'.'.join(key_path)} updated successfully."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to update uaa.yml: {e}"}

def _png_to_base64(png_path: str) -> str:
    """Converts a PNG image file to a base64 encoded string."""
    with open(png_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

def _update_banner_logo_encoded(destination_path: str, logo: str):
    """Updates the banner logo in the uaa.yml file."""
    return _update_branding_value(destination_path, ['banner', 'logo'], logo)

def update_banner_logo(destination_path: str, png_path: str):
    """Updates the banner logo (PNG format) in the uaa.yml file."""
    logo = _png_to_base64(png_path)
    return _update_branding_value(destination_path, ['banner', 'logo'], logo)

def update_banner_text(destination_path: str, text: str):
    """Updates the banner text in the uaa.yml file."""
    return _update_branding_value(destination_path, ['banner', 'text'], text)

def update_banner_text_color(destination_path: str, color: str):
    """Updates the banner text color in the uaa.yml file."""
    return _update_branding_value(destination_path, ['banner', 'textColor'], color)

def update_banner_background_color(destination_path: str, color: str):
    """Updates the banner background color in the uaa.yml file."""
    return _update_branding_value(destination_path, ['banner', 'backgroundColor'], color)

def update_banner_link(destination_path: str, link: str):
    """Updates the banner link in the uaa.yml file."""
    return _update_branding_value(destination_path, ['banner', 'link'], link)

def update_company_name(destination_path: str, name: str):
    """Updates the company name in the uaa.yml file."""
    return _update_branding_value(destination_path, ['companyName'], name)

def _update_product_logo_encoded(destination_path: str, logo: str):
    """Updates the product logo in the uaa.yml file."""
    return _update_branding_value(destination_path, ['productLogo'], logo)

def update_product_logo(destination_path: str, png_path: str):
    """Updates the product logo (PNG format) in the uaa.yml file."""
    logo = _png_to_base64(png_path)
    return _update_product_logo_encoded(destination_path, logo)

def _update_square_logo_encoded(destination_path: str, logo: str):
    """Updates the square logo in the uaa.yml file."""
    return _update_branding_value(destination_path, ['squareLogo'], logo)

def update_square_logo(destination_path: str, png_path: str):
    """Updates the square logo (PNG file) in the uaa.yml file."""
    logo = _png_to_base64(png_path)
    return _update_square_logo_encoded(destination_path, logo)

def update_footer_legal_text(destination_path: str, text: str):
    """Updates the footer legal text in the uaa.yml file."""
    return _update_branding_value(destination_path, ['footerLegalText'], text)

def update_footer_links(destination_path: str, links: dict):
    """Updates the footer links in the uaa.yml file."""
    return _update_branding_value(destination_path, ['footerLinks'], links)
