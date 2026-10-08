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

## Testing Locally with AWS SAM

Requires the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).

All commands below should be run from the root of the project (i.e. the same directory as the Dockerfile).

### Build

```shell
make sam-build
```

### Invoking Lambda via HTTP requests

Runs the SAM-built container as a local HTTP server, similar to how the deployed Lambda is invoked via its Function URL.

1. Start the HTTP server:

   ```shell
   make sam-http-run
   ```

   This starts a server at `http://localhost:3000`.

2. In another terminal, send a test request:

   ```shell
   make sam-http-ping
   ```

   This sends a test request to the server you just started in step 1

3. The response should include the following:
   ```shell
   HTTP/1.1 307 TEMPORARY REDIRECT
   Location: https://mit-borrowdirect.reshare.indexdata.com/Search/Results?type=title&lookfor=basketball
   ```



## Environment Variables

### Required

```shell
SENTRY_DSN=### If set to a valid Sentry DSN, enables Sentry exception monitoring. This is not needed for local development.
WORKSPACE=### Set to `dev` for local development, this will be set to `stage` and `prod` in those environments by Terraform.
```

## Related Assets
* Infrastructure: [mitlib-tf-workloads-wcd2reshare](https://github.com/MITLibraries/mitlib-tf-workloads-wcd2reshare)



