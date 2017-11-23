import json,logging,requests,os,pyjq

from requests import *

def getLogger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    return logger

def oauth_authentication(shard, refresh_token):
    session = Session()
    uri = "https://{}/api/oauth2".format(shard)
    data = {
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    headers = {
        "X-Api-Version": "1.5",
        "content-type": "application/json"
    }
    response = session.post(uri, headers=headers, data=json.dumps(data))
    response_json_obj = json.loads(response.text)
    return response_json_obj

def grs_list_projects(access_token):
    logger = getLogger()
    session = Session()
    uri = "https://{}/grs/orgs/{}/projects".format(os.environ['shard'],os.environ['org_id'])
    headers = {
        "X-API-Version": "2.0",
        "Authorization": "Bearer {}".format(access_token),
        "content-type": "application/json"
    }
    project_list_response = session.get(uri, headers=headers)
    project_list_json_object = json.loads(project_list_response.text)
    return project_list_json_object

def ca_add_markup(access_token, account_href, public_cloud_vendors, name, percentage):
    session = Session()
    uri = "https://pricing.rightscale.com/api/markups"
    headers = {
        "X-API-Version": "1.0",
        "Authorization": "Bearer {}".format(access_token),
        "content-type": "application/json"
    }
    data = {
        "name": name,
        "account_href": account_href,
        "percentage": percentage,
        "public_cloud_vendors": public_cloud_vendors
    }
    # TODO: Evaluate the response and report errors
    markup_response = session.post(uri, headers=headers, data=json.dumps(data))

def ca_remove_markup(access_token, markup_href):
    session = Session()
    headers = {
        "X-API-Version": "1.0",
        "Authorization": "Bearer {}".format(access_token),
        "content-type": "application/json"
    }
    # TODO: Evaluate the response and report errors
    markup_response = session.delete(markup_href, headers=headers)

def ca_list_markups(access_token):
    logger = getLogger()
    session = Session()
    uri = "https://pricing.rightscale.com/api/markups"
    headers = {
        "X-API-Version": "1.0",
        "Authorization": "Bearer {}".format(access_token),
        "content-type": "application/json"
    }
    markup_response = session.get(uri, headers=headers)
    return json.loads(markup_response.text)

def add_markup_handler(event, context):
    logger = getLogger()
    # Get access token first
    response_json_obj = oauth_authentication(
        os.environ['shard'],
        os.environ['refresh_token']
        )
    access_token = response_json_obj['access_token']
    projects = grs_list_projects(access_token)
    existing_markups = ca_list_markups(access_token)

    for project in projects:
        logger.info("Operating on project {} ({})".format(project['name'], project['id']))
        jq_query = '.[] | select(.account_href == "/api/accounts/{}" and .name == "BULK ADDED - AWS") | .href'.format(project['id'])
        existing_aws_markups = pyjq.all(jq_query, existing_markups)
        if len(existing_aws_markups) == 0:
            # AWS
            ca_add_markup(
                access_token,
                "/api/accounts/{}".format(project['id']),
                ["Amazon Web Services"],
                "BULK ADDED - AWS",
                os.environ['aws_markup_percent']
            )
        else:
            logger.info("AWS Markup already existed for project {}".format(project['id']))

        jq_query = '.[] | select(.account_href == "/api/accounts/{}" and .name == "BULK ADDED - Azure") | .href'.format(project['id'])
        existing_azure_markups = pyjq.all(jq_query, existing_markups)
        if len(existing_azure_markups) == 0:
            # Azure
            ca_add_markup(
                access_token,
                "/api/accounts/{}".format(project['id']),
                ["Microsoft Azure","Azure Resource Manager"],
                "BULK ADDED - Azure",
                os.environ['azure_markup_percent']
            )
        else:
            logger.info("Azure Markup already existed for project {}".format(project['id']))


def remove_markup_handler(event, context):
    logger = getLogger()
    # Get access token first
    response_json_obj = oauth_authentication(
        os.environ['shard'],
        os.environ['refresh_token']
        )
    access_token = response_json_obj['access_token']
    # TODO: This could conceivably iterate over everything that belongs to a
    # project in the org, and which has a markup with the specified name(s).
    # Right now, I'm just using it for manual cleanup.
    ca_remove_markup(access_token, 'https://pricing.rightscale.com/api/markups/1038')
