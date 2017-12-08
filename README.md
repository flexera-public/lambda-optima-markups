# lambda-optima-markups
A python lambda function for adding RightScale Optima markups

# Usage
Generate a RightScale oAuth [token](http://docs.rightscale.com/cm/dashboard/settings/account/enable_oauth#overview)

Upload the following CAT files to RightScale SelfService - [Upload directions here](http://docs.rightscale.com/ss/guides/ss_testing_CATs.html#uploading-the-cat)
* [Sys log library](https://raw.githubusercontent.com/rightscale/rightscale-plugins/f01625b856cb4743ecb1f4ee3093bb39c3e81810/libraries/sys_log.rb)
* [AWS Cloud Formation Plugin](https://raw.githubusercontent.com/rightscale/rightscale-plugins/f01625b856cb4743ecb1f4ee3093bb39c3e81810/aws/rs_aws_cft/aws_cft_plugin.rb)
* [AWS Lambda Plugin](https://raw.githubusercontent.com/rightscale/rightscale-plugins/f01625b856cb4743ecb1f4ee3093bb39c3e81810/aws/rs_aws_lambda/aws_lambda_plugin.rb)
* [Lambda Optima Markups](scheduler.cat.rb)

Launch CloudApp

Prosper
