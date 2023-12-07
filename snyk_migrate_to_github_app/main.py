"""Primary logic for the CLI Tool
"""

# ===== IMPORTS =====

import json

import requests
import typer
from rich import print
from typing_extensions import Annotated

# ===== CONSTANTS =====

SNYK_V1_API_BASE_URL        = 'https://snyk.io/api/v1'
SNYK_REST_API_BASE_URL      = 'https://api.snyk.io/rest'
SNYK_REST_API_VERSION       = '2023-11-27~beta'
SNYK_HIDDEN_API_BASE_URL    = 'https://api.snyk.io/hidden'
SNYK_HIDDEN_API_VERSION     = '2023-04-02~experimental'
SNYK_API_TIMEOUT_DEFAULT    = 90

# ===== GLOBALS =====

app = typer.Typer(add_completion=False)
state = {"verbose": False}

# ===== METHODS =====

@app.command()
def main(
    org_id:
        Annotated[
            str,
            typer.Argument(
                help='ID of Organization in Snyk you wish to migrate targets to GitHub App',
                envvar='SNYK_ORG_ID')],
    snyk_token:
        Annotated[
            str,
            typer.Argument(
                help='Snyk API token, or set as environment variable',
                envvar='SNYK_TOKEN')],
    dry_run:
        Annotated[
            bool,
            typer.Option(
                help='Print names of targets to be migrated without migrating')] = False,
    include_github_targets:
        Annotated[
            bool,
            typer.Option(
                help='Migrate both github and github-enterprise projects, default is only github-enterprise')] = False,
    verbose: bool = False):
    """CLI Tool to help you migrate your targets from the GitHub or GitHub Enterprise integration to the new GitHub App Integration
    """
    if verbose:
        state["verbose"] = True

    if verify_org_integrations(snyk_token, org_id):
        targets = get_all_targets(snyk_token, org_id)

        if include_github_targets:
            targets.extend(get_all_targets(snyk_token, org_id, origin='github'))

        if (dry_run):
            dry_run_targets(targets)
        else:
            migrate_targets(snyk_token, org_id, targets)

def verify_org_integrations(snyk_token, org_id):
    """Helper function to make sure the Snyk Organization has the relevant github integrations set up

    Args:
        snyk_token (str): Snyk API token
        org_id (str): Snyk Organization ID

    Returns:
        bool: _description_
    """
    headers = {
        'Authorization': f'token {snyk_token}'
    }

    url = f"{SNYK_V1_API_BASE_URL}/org/{org_id}/integrations"

    response = requests.request(
        'GET',
        url,
        headers=headers,
        timeout=SNYK_API_TIMEOUT_DEFAULT
    )

    if response.status_code != 200:
        print(f"Unable to retrieve integrations for Snyk org: {org_id}, reason: {response.status_code}")
        return False

    integrations = json.loads(response.content)

    if ('github-enterprise' not in integrations and
        'github' not in integrations):

        print(f"No GitHub or GitHub Enterprise integration detected for Snyk Org: {org_id}")
        return False

    if ('github-cloud-app' not in integrations):

        print(f"No GitHub Cloud App integration detected for Snyk Org: {org_id}, please set up before migrating GitHub or GitHub Enterprise targets")
        return False

    return True

def get_all_targets(snyk_token, org_id, origin='github-enterprise'):
    """Helper function to retrieve targets in an org

    Args:
        snyk_token (str): Snyk API token
        org_id (str): Snyk Organization ID
        origin (str, optional): Filter to retrieve targets of a certain origin. Defaults to 'github-enterprise'.

    Returns:
        list: github targets in a snyk org
    """

    targets = []

    headers = {
        'Authorization': f'token {snyk_token}'
    }

    url = f'{SNYK_REST_API_BASE_URL}/orgs/{org_id}/targets?version={SNYK_REST_API_VERSION}&limit=100&origin={origin}'

    while True:
        response = requests.request(
            'GET',
            url,
            headers=headers,
            timeout=SNYK_API_TIMEOUT_DEFAULT)

        response_json = json.loads(response.content)

        if 'data' in response_json:
            targets = targets + response_json['data']

        if 'next' not in response_json['links'] or response_json['links']['next'] == '':
            break
        url = f"{SNYK_REST_API_BASE_URL}/{response_json['links']['next']}"

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

def migrate_targets(snyk_token, org_id, targets):
    """Helper function to migrate list of github and github-enterprise targets to github-cloud-app

    Args:
        snyk_token (str): Snyk API token
        org_id (str): Snyk Organization ID
        targets (list): List of targets to be migrated
    """
    headers = {
        'Content-Type': 'application/vnd.api+json',
        'Authorization': f'token {snyk_token}'
    }

    for target in targets:
        url = f"{SNYK_HIDDEN_API_BASE_URL}/orgs/{org_id}/targets/{target['id']}?version={SNYK_HIDDEN_API_VERSION}"

        body = json.dumps({
            "data": {
                "id": f"{target['id']}",
                "attributes": {
                    "source_type": "github-cloud-app"
                }
            }
        })

        response = requests.request(
            "PATCH",
            url,
            headers=headers,
            data=body,
            timeout=SNYK_API_TIMEOUT_DEFAULT)

        if response.status_code == 200:
            print(f"Migrated target: {target['id']} {target['attributes']['displayName']} to github-cloud-app")
        elif response.status_code == 409:
            print(f"Unable to migrate target: {target['id']} {target['attributes']['displayName']} to github-cloud-app because it has already been migrated")
        else:
            print(f"Unable to migrate target: {target['id']} {target['attributes']['displayName']} to github-cloud-app, reason: {response.status_code}")

def run():
    """Run the defined typer CLI app
    """
    app()
