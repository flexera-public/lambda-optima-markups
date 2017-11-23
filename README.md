# lambda-optima-markups
A python lambda function for adding RightScale Optima markups

# Environment Variables
The Python script requires the following environment variables.

* aws_markup_percent: The percentage markup you'd like to add for AWS in Optima
* azure_markup_percent: The percentage markup you'd like to add for Azure in Optima
* org_id: The ID of your RightScale organization
* refresh_token: Your RightScale oAuth refresh token
* shard: The hostname of the RightScale shard you're using (us-3.rightscale.com, us-4.rightscale.com, telstra-10.rightscale.com)
