name 'lambda-optima-markup scheduler'
rs_ca_ver 20161221
short_description "Optima Markup Scheduler"
long_description "Version: 1.0"
import "plugins/rs_aws_lambda"

resource "optima_markup_function", type: "rs_aws_lambda.function" do
  function_name "optima-markup-function"
  description "Optima Markup Function"
  runtime "python3.6"
  handler "optima_markups.add_markup_handler"
  # TODO: Override this with the AWS_ACCOUNT_ID environment variable
  role "arn:aws:iam::385266030856:role/service-role/readonly"
end

operation "launch" do
  definition "launch"
end

define launch(@optima_markup_function) do
  $optima_markup_function = to_object(@optima_markup_function)
  $zipfile_response = http_get(url: "https://github.com/rs-services/lambda-optima-markups/releases/download/untagged-2c38c9f3b9b099cbd6e8/lambda-optima-markups.zip")
  $base64_zip = to_base64($zipfile_response['body'])
  $optima_markup_function['fields']['code'] = {
    'ZipFile': $base64_zip
  }
  @optima_markup_function = $optima_markup_function
  provision(@optima_markup_function)
end
