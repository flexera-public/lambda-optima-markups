# lambda-optima-markups
A python lambda function for adding RightScale Optima markups to all accounts in an organization.

# Usage
1. Generate a RightScale oAuth [token](http://docs.rightscale.com/cm/dashboard/settings/account/enable_oauth#overview)
1. Create a RightScale [Credential](http://docs.rightscale.com/cm/dashboard/design/credentials/index.html#create-a-new-credential) with the value of the refresh token.
1. Choose an existing S3 bucket (or create a new one) where the lambda functions will be uploaded.
1. Upload the following CAT files to RightScale SelfService - [Upload directions here](http://docs.rightscale.com/ss/guides/ss_testing_CATs.html#uploading-the-cat)
  * [Sys log library](https://raw.githubusercontent.com/rightscale/rightscale-plugins/f01625b856cb4743ecb1f4ee3093bb39c3e81810/libraries/sys_log.rb)
  * [AWS Cloud Formation Plugin](https://raw.githubusercontent.com/rightscale/rightscale-plugins/f01625b856cb4743ecb1f4ee3093bb39c3e81810/aws/rs_aws_cft/aws_cft_plugin.rb)
  * [AWS Lambda Plugin](https://raw.githubusercontent.com/rightscale/rightscale-plugins/f01625b856cb4743ecb1f4ee3093bb39c3e81810/aws/rs_aws_lambda/aws_lambda_plugin.rb)
  * [Lambda Optima Markups](scheduler.cat.rb)
1. Launch CloudApp using the appropriate values from steps 2 and 3
1. Prosper
