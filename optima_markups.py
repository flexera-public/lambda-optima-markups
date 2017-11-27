# -*- coding: utf-8 -*-
""" A simple set of methods for interacting with the RightScale pricing API for
the purpose of manipulating markups"""
import json,logging,requests,os,pyjq

from requests import *

def getLogger():
    """ Initializes and returns a logger. The log level is always DEBUG

    Returns:
        Logger: An initalized logger, set to log at the DEBUG level

    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    return logger

def oauth_authentication(shard, refresh_token):
    """Authenticates with the RightScale API and returns the json response as a
    dict

    Args:
        shard (:obj:`str`): The RightScale shard hostname (I.E
            us-3.rightscale.com, us-4.rightscale.com, telstra-10.rightscale.com)
        refresh_token (:obj:`str`): A RightScale oAuth API RefreshToken (see:
            http://docs.rightscale.com/api/api_1.5_examples/oauth.html#obtaining-an-oauth-grant)

    Returns:
        :obj:`dict`: The API response as a dict. (see:
            http://reference.rightscale.com/api1.5/resources/ResourceOauth2.html#create)
    """
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
    """Returns the list of all RightScale projects (accounts) belonging to the
    org specified in the `org_id` environment variable.

    Args:
        access_token (:obj:`str`): A RightScale API access token returned by
            oauth_authentication()

    Returns:
        :obj:`dict`: The an object representing the JSON payload of this API
            call (https://s3.amazonaws.com/rs-docs-staging/platform/grs/rb_staging_20171013.185312/index.html#/2.0/controller/V2-Definitions-Projects)
    """
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
    """Adds the specified markup to the specified account/cloud combination

    Args:
        access_token (:obj:`str`): A RightScale API access token returned by
            oauth_authentication()
        account_href (:obj:`str`): The (legacy) RightScale account href (I.E
            /api/accounts/<acct_id>) of the account to receive the markup.
        public_cloud_vendors (:obj:`list` of :obj:`str`): The list of cloud
            vendors to apply the markup to. (see: http://reference.rightscale.com/cloud_analytics/pricing_api/#/1.0/controller/V1-ApiResources-Markups/create)
        name (:obj:`str`): The name of the markup to apply
        percentage (float): The percentage markup to apply

    Returns:
        :obj:`dict`: The an object representing the JSON payload of this API
            call (http://reference.rightscale.com/cloud_analytics/pricing_api/#/1.0/controller/V1-ApiResources-Markups/create)
    """
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
    """Adds the specified markup to the specified account/cloud combination

    Args:
        access_token (:obj:`str`): A RightScale API access token returned by
            oauth_authentication()
        markup_href (:obj:`str`): The markup href to destroy/remove

    Returns:
        :obj:`dict`: The an object representing the JSON payload of this API
            call (http://reference.rightscale.com/cloud_analytics/pricing_api/#/1.0/controller/V1-ApiResources-Markups/destroy)
    """
    session = Session()
    headers = {
        "X-API-Version": "1.0",
        "Authorization": "Bearer {}".format(access_token),
        "content-type": "application/json"
    }
    # TODO: Evaluate the response and report errors
    markup_response = session.delete(markup_href, headers=headers)

def ca_list_markups(access_token):
    """Lists all markups visible to the authenticated user

    Args:
        access_token (:obj:`str`): A RightScale API access token returned by
            oauth_authentication()

    Returns:
        :obj:`dict`: The an object representing the JSON payload of this API
            call (http://reference.rightscale.com/cloud_analytics/pricing_api/#/1.0/controller/V1-ApiResources-Markups/index)
    """
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
    """A lambda event handler which (idempotently) adds the desired markups to
    both AWS and Azure cloud(s).

    It uses the value in the environment variable `aws_markup_percent` for AWS.

    It uses the value in the enviornment variable `azure_markup_percent` for Azure.

    It (idempotnently) applies the markup to all projects (accounts) in the
    organization specified in the environment variable `org_id`

    Args:
        event (:obj:`multiple`): AWS Lambda event data
        context (:obj:`LambdaContext`): AWS Lambda context data
    """
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
