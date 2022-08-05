# wcd2reshare
redirect from Worldcat Discovery to BorrowDirect / VuFind

## Required ENV
`SENTRY_DSN` = If set to a valid Sentry DSN, enables Sentry exception monitoring. This is not needed for local development.

`WORKSPACE` = Set to `dev` for local development, this will be set to `stage` and `prod` in those environments by Terraform.

## Developing locally

<https://docs.aws.amazon.com/lambda/latest/dg/images-test.html>

### Makefile commands for installation and dependency management

```bash
make install # installs with dev dependencies
make test # runs tests and outputs coverage report
make lint # runs code linting, quality, and safety checks
make update # updates dependencies
```

### Build the container

```bash
make dist-dev
```

### Run the default handler for the container 

```bash
docker run -e WORKSPACE=dev -p 9000:8080 wcd2reshare-dev:latest
```

### POST to the container. 

```bash
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"queryStringParameters":{"rft.title": "baseketball"}}'
```

### Observe output

```json
{
    "headers": {
        "Location": "https://borrowdirect.reshare.indexdata.com/Search/Results?type=title&lookfor=baseketball"
    },
    "statusCode": 307
}
```
NOTE: The POST command and observed output above will verify that the lambda_handler function is 
working as expected from within the container. The Lambda *function url* cannot be tested locally
and has to be verified in AWS dev.