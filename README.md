![snyk-oss-category](https://github.com/snyk-labs/oss-images/blob/main/oss-community.jpg)

# Migrate to GitHub Cloud App

## Introduction

This tool is designed to help you easily migrate your Snyk Targets that were imported using either the existing GitHub or GitHub Enterprise integrations to the new GitHub Cloud App or GitHub Server App integrations. Below, you will learn how to install the tool and how to run the tool.

## Installation

### Clone Source and Run

The first option is to `git clone` this repository and run the tool using `poetry`

**Requirements**

* Python version >=3.11
* Poetry installed:
  * Can be installed with pip: `pip install poetry`

**Steps**

* Clone this repo and change directory
* Install the dependencies using poetry
```shell
poetry install
```
* Run the CLI using poetry
```shell
poetry run snyk-migrate-to-github-app --help
```
* You should see the Usage instructions printed
* Alternatively you can launch a python virtual env shell with poetry and run the tool
```shell
poetry shell
poetry install
snyk-migrate-to-github-app --help
```

## Using the Tool

All you need to run the tool is a [Snyk API token](https://docs.snyk.io/getting-started/how-to-obtain-and-authenticate-with-your-snyk-api-token) and the Organization ID of the Organization where you want to migrate your targets to the new GitHub Cloud App or GitHub Server App

**Before Running the Tool:** It is assumed that the GitHub Cloud App integration has already been configured in the Snyk Organization where you will be migrating targets

To show the usage in the terminal
```shell
snyk-migrate-to-github-app --help
```

The primary way to run the tool
```shell
snyk-migrate-to-github-app <ORG_ID> <SNYK_TOKEN>
```
Where:

* `<SNYK_TOKEN>` is your Snyk API token
* `<ORG_ID>` is your Snyk Organization ID where you want to migrate targets to the new GitHub Cloud App

Alternatively, instead of passing the Snyk Token and Org ID in line, you can define them as environment variables; SNYK_TOKEN & SNYK_ORG_ID

```shell
export SNYK_TOKEN=<YOUR_SNYK_TOKEN>
export SNYK_ORG_ID=<YOUR_ORGANIZATION_ID>
snyk-migrate-to-github-app
```

By default, it is assumed you are migrating to the GitHub Cloud App. If you want to migrate to the GitHub Server App, include the flag as follows

```shell
snyk-migrate-to-github-app <ORG_ID> <SNYK_TOKEN> --github-server-app
```

Running the tool will immediately start the migration process. However, you may want to see which projects will be migrated before you start the migration process. You can run the tool with the `--dry-run` option which will only print the effected targets to the terminal without actually migrating them

```shell
snyk-migrate-to-github-app <ORG_ID> <SNYK_TOKEN> --dry-run
```

You can specify EU or AU tenants with the `--tenant` option

```shell
# EU Tenant
snyk-migrate-to-github-app <ORG_ID> <SNYK_TOKEN> --tenant=eu

# AU Tenant
snyk-migrate-to-github-app <ORG_ID> <SNYK_TOKEN> --tenant=au
```

By default, only targets imported with the *GitHub Enterprise* integration will be migrated to the new GitHub Cloud App. If you wish to also include targets that were imported with the *GitHub* integration as well, you can pass the `--include-github-targets` option
```shell
snyk-migrate-to-github-app <ORG_ID> <SNYK_TOKEN> --include-github-targets
```