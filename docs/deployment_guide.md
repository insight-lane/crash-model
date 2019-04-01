## Deployment strategies

We currently support two deployment strategies: On AWS through Docker and as a statically hosted website

#### Deploying on a existing S3 bucket

* Create your S3 bucket following the AWS [guide](https://docs.aws.amazon.com/quickstarts/latest/s3backup/step-1-create-bucket.html) to do so.
* Set your bucket permissions to be public.
* Upload index.html, js and css folders to the bucket. Remember to grant public access to the files.
* Thats it! Now navigate to https://s3.amazonaws.com/[your-bucket-name]/index.html to view the demo!

We are currently hosting the showcase on S3 at [https://s3.amazonaws.com/crash-model/index.html](https://s3.amazonaws.com/crash-model/index.html)