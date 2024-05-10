"""Primary logic for the CLI Tool
"""

# ===== IMPORTS =====

import json

import requests
import typer
from rich import print
from typing_extensions import Annotated

# ===== CONSTANTS =====

SNYK_V1_API_BASE_URL = "https://snyk.io/api/v1"
SNYK_V1_API_BASE_URL_AU = "https://api.au.snyk.io/v1"
SNYK_V1_API_BASE_URL_EU = "https://api.eu.snyk.io/v1/"
SNYK_REST_API_BASE_URL = "https://api.snyk.io/rest"
SNYK_REST_API_BASE_URL_AU = "https://api.au.snyk.io/rest"
SNYK_REST_API_BASE_URL_EU = "https://api.eu.snyk.io/rest"
SNYK_REST_API_VERSION = "2023-11-27~beta"
SNYK_HIDDEN_API_BASE_URL = "https://api.snyk.io/hidden"
SNYK_HIDDEN_API_BASE_URL_AU = "https://api.au.snyk.io/hidden"
SNYK_HIDDEN_API_BASE_URL_EU = "https://api.eu.snyk.io/hidden"
SNYK_HIDDEN_API_VERSION = "2023-04-02~experimental"
SNYK_API_TIMEOUT_DEFAULT = 90

# ===== GLOBALS =====

app = typer.Typer(add_completion=False)
state = {"verbose": False}

# ===== METHODS =====


@app.command()
def main(  # pylint: disable=too-many-arguments
    org_id: Annotated[
        str,
        typer.Argument(
            help="ID of Organization in Snyk you wish to migrate targets to GitHub App",
            envvar="SNYK_ORG_ID",
        ),
    ],
    snyk_token: Annotated[
        str,
        typer.Argument(
            help="Snyk API token, or set as environment variable", envvar="SNYK_TOKEN"
        ),
    ],
    tenant: Annotated[
        str, typer.Option(help="Defaults to US tenant, add 'eu' or 'au'")
    ] = "",
    dry_run: Annotated[
        bool,
        typer.Option(help="Print names of targets to be migrated without migrating"),
    ] = False,
    include_github_targets: Annotated[
        bool,
        typer.Option(
            help="Migrate both github and github-enterprise projects, default is only github-enterprise"
        ),
    ] = False,
    verbose: bool = False,
):
    """CLI Tool to help you migrate your targets from the GitHub or GitHub Enterprise integration to the new GitHub App Integration"""
    if verbose:
        state["verbose"] = True

    if tenant not in ("", "au", "eu"):
        print(f"Invalid tenant: {tenant}")
        print("Must me either 'eu' or 'au'")
        return

    if verify_org_integrations(snyk_token, org_id, tenant=tenant):
        targets = get_all_targets(snyk_token, org_id, tenant=tenant)

        if include_github_targets:
            targets.extend(
                get_all_targets(snyk_token, org_id, origin="github", tenant=tenant)
            )

        if dry_run:
            dry_run_targets(targets)
        else:
            migrate_targets(snyk_token, org_id, targets, tenant=tenant)


def verify_org_integrations(snyk_token, org_id, tenant=""):
    """Helper function to make sure the Snyk Organization has the relevant github integrations set up

    Args:
        snyk_token (str): Snyk API token
        org_id (str): Snyk Organization ID
        tenant (str, optional): Snyk tenant

    Returns:
        bool: _description_
    """
    headers = {"Authorization": f"token {snyk_token}"}

    base_url = SNYK_V1_API_BASE_URL

    if tenant == "au":
        base_url = SNYK_V1_API_BASE_URL_AU
    if tenant == "eu":
        base_url = SNYK_V1_API_BASE_URL_EU

    url = f"{base_url}/org/{org_id}/integrations"

    try:
        response = requests.request(
            "GET", url, headers=headers, timeout=SNYK_API_TIMEOUT_DEFAULT
        )
    except requests.ConnectionError:
        print(f"Unable to connect to {base_url}")
        return False

    if response.status_code != 200:
        print(
            f"Unable to retrieve integrations for Snyk org: {org_id}, reason: {response.status_code}"
        )
        return False

    integrations = json.loads(response.content)

    if "github-enterprise" not in integrations and "github" not in integrations:

        print(
            f"No GitHub or GitHub Enterprise integration detected for Snyk Org: {org_id}"
        )
        return False

    if "github-cloud-app" not in integrations:

        print(
            f"No GitHub Cloud App integration detected for Snyk Org: {org_id}, please set up before migrating GitHub or GitHub Enterprise targets"
        )
        return False

    return True


def get_all_targets(snyk_token, org_id, origin="github-enterprise", tenant=""):
    """Helper function to retrieve targets in an org

    Args:
        snyk_token (str): Snyk API token
        org_id (str): Snyk Organization ID
        origin (str, optional): Filter to retrieve targets of a certain origin. Defaults to 'github-enterprise'.
        tenant (str, optional): Snyk tenant

    Returns:
        list: github targets in a snyk org
    """

    targets = []

    headers = {"Authorization": f"token {snyk_token}"}

    base_url = SNYK_REST_API_BASE_URL

    if tenant == "au":
        base_url = SNYK_REST_API_BASE_URL_AU
    if tenant == "eu":
        base_url = SNYK_REST_API_BASE_URL_EU

    url = f"{base_url}/orgs/{org_id}/targets?version={SNYK_REST_API_VERSION}&limit=100&origin={origin}&excludeEmpty=false"

    while True:
        response = requests.request(
            "GET", url, headers=headers, timeout=SNYK_API_TIMEOUT_DEFAULT
        )

        response_json = json.loads(response.content)

        if "data" in response_json:
            targets = targets + response_json["data"]

        if "next" not in response_json["links"] or response_json["links"]["next"] == "":
            break
        url = f"{base_url}/{response_json['links']['next']}"

    return targets


def dry_run_targets(targets):
    """Print targets that would get migrated to GitHub App integration without migrating them

    Args:
        targets: List of targets to be logged
    """
    for target in targets:
        print(f"Target: {target['id']}, Name: {target['attributes']['displayName']}")

    print()
    print(f"Total Targets: {len(targets)}")


def migrate_targets(snyk_token, org_id, targets, tenant=""):
    """Helper function to migrate list of github and github-enterprise targets to github-cloud-app

    Args:
        snyk_token (str): Snyk API token
        org_id (str): Snyk Organization ID
        targets (list): List of targets to be migrated
        tenant (str, optional): Snyk tenant
    """

    base_url = SNYK_HIDDEN_API_BASE_URL

    if tenant == "au":
        base_url = SNYK_HIDDEN_API_BASE_URL_AU
    if tenant == "eu":
        base_url = SNYK_HIDDEN_API_BASE_URL_EU

    headers = {
        "Content-Type": "application/vnd.api+json",
        "Authorization": f"token {snyk_token}",
    }

    for target in targets:
        url = f"{base_url}/orgs/{org_id}/targets/{target['id']}?version={SNYK_HIDDEN_API_VERSION}"

        body = json.dumps(
            {
                "data": {
                    "id": f"{target['id']}",
                    "attributes": {"source_type": "github-cloud-app"},
                }
            }
        )

        response = requests.request(
            "PATCH", url, headers=headers, data=body, timeout=SNYK_API_TIMEOUT_DEFAULT
        )

        if response.status_code == 200:
            print(
                f"Migrated target: {target['id']} {target['attributes']['displayName']} to github-cloud-app"
            )
        elif response.status_code == 409:
            print(
                f"Unable to migrate target: {target['id']} {target['attributes']['displayName']} to github-cloud-app because it has already been migrated"
            )
        else:
            print(
                f"Unable to migrate target: {target['id']} {target['attributes']['displayName']} to github-cloud-app, reason: {response.status_code}"
            )


def run():
    """Run the defined typer CLI app"""
    app()
