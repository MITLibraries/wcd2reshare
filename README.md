# wcd2reshare
wcd2reshare is a 'middleware' layer between Worldcat Discovery and the ReShare / BorrowDirect service's VuFind catalog. 

When Worldcat Discovery directs users to BorrowDirect for fulfillment options, it can only do so via openURL formatted URLs, which VuFind does not understand. 

To address this issue, we configure the outgoing links from Worldcat Discovery to BorrowDirect to use the function URL for this Lambda (rather than the URL for BorrowDirect). 

When the Lambda receives the openURL query from Worldcat Discovery, it reformats the search query to the format required by VuFind, and redirects the user's browser to VuFind with the transformed search query.

Because the metadata backing Worldcat Discovery may differ from the metadata backing BorrowDirect, and because of how search strings for VuFind must be constructed, the app builds an array of VuFind search strings using the OpenURL metadata from Worldcat, trying each of them against the BorrowDirect search API.  The first search string that produces results at BorrowDirect is the one selected and used when the user's browser is redirected to BorrowDirect.

## Development

- To preview a list of available Makefile commands: `make help`
- To install with dev dependencies: `make install`
- To update dependencies: `make update`
- To run unit tests: `make test`
- To lint the repo: `make lint`


## Running Locally with Docker

<https://docs.aws.amazon.com/lambda/latest/dg/images-test.html>

- Build the container:

```bash
  docker build -t wcd2reshare:latest .
  ```

- Run the default handler for the container: 

```bash
docker run -e WORKSPACE=dev -p 9000:8080 wcd2reshare:latest
```

- POST to the container: 

```bash
curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d '{"queryStringParameters":{"rft.title": "baseketball"}}'
```

- Observe output:

```json
{
    "headers": {
        "Location": "https://borrowdirect.reshare.indexdata.com/Search/Results?type=title&lookfor=baseketball"
    },
    "statusCode": 307
}
```

## Environment Variables

### Required

```shell
SENTRY_DSN=### If set to a valid Sentry DSN, enables Sentry exception monitoring. This is not needed for local development.
WORKSPACE=### Set to `dev` for local development, this will be set to `stage` and `prod` in those environments by Terraform.
```

## Related Assets
* Infrastructure: [mitlib-tf-workloads-wcd2reshare](https://github.com/MITLibraries/mitlib-tf-workloads-wcd2reshare)



