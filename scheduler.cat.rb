name 'lambda-optima-markup scheduler'
rs_ca_ver 20161221
short_description "Optima Markup Scheduler"
long_description "Version: 1.0"
import "plugins/rs_aws_lambda"
import "plugins/rs_aws_cft"
import "rjg/libs/s3_lambda_inception"

parameter "param_bucket" do
  label "S3 Bucket"
  type "string"
  description "An S3 bucket where lambda deployment packages will be uploaded"
  operations ['launch']
end

parameter "param_refresh_token" do
  label "Refresh Token"
  type "string"
  description "json:{\"definition\":\"getCredentials\", \"description\":\"A RightScale credential containing the refresh token which should be used for the lambda function to authenticate.\"}"
  operations ['launch', 'markup']
end

parameter "param_aws_markup" do
  label "AWS Markup Percent"
  type "string"
  description "The markup percentage for all AWS clouds in all accounts in the organization"
  default "0.1"
  operations ['launch', 'markup']
end

parameter "param_azure_markup" do
  label "Azure Markup Percent"
  type "string"
  description "The markup percentage for all Azure clouds in all accounts in the organization"
  default "0.1"
  operations ['launch', 'markup']
end

parameter "param_frequency" do
  label "Execution Frequency"
  type "number"
  description "The frequency (in minutes) that the markup Lambda function should be executed"
  default 10
end

output "out_org" do
  label "Organization"
  default_value "Default (will be overwritten)"
end

mapping "mapping_shards" do {
  "/api/clusters/3" => {
    "grs" => "us-3.rightscale.com",
    "cm" => "us-3.rightscale.com",
    "ss" => "selfservice-3.rightscale.com"
  },
  "/api/clusters/4" => {
    "grs" => "us-4.rightscale.com",
    "cm" => "us-4.rightscale.com",
    "ss" => "selfservice-4.rightscale.com"
  },
  "/api/clusters/10" => {
    "grs" => "telstra-10.rightscale.com",
    "cm" => "telstra-10.rightscale.com",
    "ss" => "selfservice-10.rightscale.com"
  }
} end

resource "lambda_role_stack", type: "rs_aws_cft.stack" do
  like @s3_lambda_inception.lambda_role_stack
  parameter_1_value $param_bucket
end

resource "s3_lambda_inception_function", type: "rs_aws_lambda.function" do
  like @s3_lambda_inception.s3_lambda_inception_function
end

resource "optima_markup_function", type: "rs_aws_lambda.function" do
  function_name join(["optima-markup-function-",last(split(@@deployment.href, "/"))])
  description "Optima Markup Function"
  runtime "python3.6"
  handler "optima_markups.add_markup_handler"
  timeout "90"
  role "overwritten in launch"
  code do {
    "S3Bucket": $param_bucket,
    "S3Key": "lambda-optima-markups.zip"
  } end
end

operation "launch" do
  definition "launch"
  output_mappings do {
    $out_org => $organization
  } end
end

operation "markup" do
  definition "markup"
end

define getCredentials() return $values do
  @creds = rs_cm.credentials.index()
  $values = @creds.name[]
end

define getParameters($mapping_shards) return $user_id, $account_id, $shard_href, $org_id, $org_name do
  $response = rs_cm.session.index(view: 'whoami')
  $whoami_links = $response[0]['links']

  $user_link = last(select($whoami_links, {"rel": "user"}))
  $user_href = $user_link['href']
  $user_id = last(split($user_href, '/'))

  $account_link = last(select($whoami_links, {"rel": "account"}))
  $account_href = $account_link['href']
  $account_id = last(split($account_href, '/'))

  $account_response = rs_cm.get(href: '/api/accounts/'+$account_id)
  $account_links = $account_response[0]['links']

  $shard_link = last(select($account_links, {"rel": "cluster"}))
  $shard_href = $shard_link['href']
  $shard_href = map($mapping_shards, $shard_href, 'grs')

  $grs_user_response = http_get(url: "https://"+$shard_href+"/grs/users/"+$user_id+"/orgs?filter=legacy_account_id="+$account_id, headers: {"X-API-Version": "2.0", "content-type": "application/json"})
  $values = first($grs_user_response['body'])
  $org_id = $values['id']
  $org_name = $values['name']
end

define launch(@lambda_role_stack, @s3_lambda_inception_function, @optima_markup_function, $param_bucket, $param_frequency, $param_refresh_token, $param_aws_markup, $param_azure_markup, $mapping_shards) return @lambda_role_stack, @s3_lambda_inception_function, @optima_markup_function, $organization do
  call s3_lambda_inception.launch(@lambda_role_stack, @s3_lambda_inception_function, $param_bucket) retrieve @lambda_role_stack, @s3_lambda_inception_function

  @s3_lambda_inception_function.invoke({
    "S3_FILENAME": "lambda-optima-markups.zip",
    "S3_BUCKET": $param_bucket,
    "URI": "https://github.com/rs-services/lambda-optima-markups/releases/download/untagged-5bbc69dabffe9a07cf76/lambda-optima-markups.zip"
  })

  $optima_markup_function = to_object(@optima_markup_function)
  $optima_markup_function['fields']['role'] = sub(@lambda_role_stack.OutputValue[0], /role.*$/, "role/service-role/readonly")
  @optima_markup_function = $optima_markup_function
  provision(@optima_markup_function)

  call getParameters($mapping_shards) retrieve $user_id, $account_id, $shard_href, $org_id, $org_name

  $organization = $org_name + " - " + $org_id

  # Create Scheduled job to check approval status of issue
  $time = now() + (60*2) # Run it for the first time, two minutes from now
  rs_ss.scheduled_actions.create(
    execution_id:       @@execution.id,
    name:               "Adding Markups",
    action:             "run",
    operation:          {
      "name": "markup",
      "configuration_options": [
        { "name": "param_refresh_token", "type": "string", "value": $param_refresh_token },
        { "name": "param_aws_markup", "type": "string", "value": $param_aws_markup },
        { "name": "param_azure_markup", "type": "string", "value": $param_azure_markup }
      ]
    },
    first_occurrence:   $time,
    recurrence:         "FREQ=MINUTELY;INTERVAL=" + to_s($param_frequency)
  )
end

define markup(@optima_markup_function, $param_refresh_token, $param_aws_markup, $param_azure_markup, $mapping_shards) do
  $refresh_token = cred($param_refresh_token)
  call getParameters($mapping_shards) retrieve $user_id, $account_id, $shard_href, $org_id, $org_name
  @optima_markup_function.invoke({
    'shard': $shard_href,
    'refresh_token': $refresh_token,
    'org_id': $org_id,
    'aws_markup_percent': $param_aws_markup,
    'azure_markup_percent': $param_azure_markup
  })
end
