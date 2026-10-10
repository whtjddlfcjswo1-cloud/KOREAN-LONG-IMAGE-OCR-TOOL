# GitHub Actions staging deployment

LongImageOCR staging is deployed from GitHub Actions. Local Docker and local `gcloud` are not required.

## One-time GitHub configuration

Create a GitHub Environment named `staging` (recommended) or use repository-level Variables/Secrets.

### Required variable

- `GCP_PROJECT_ID` — Google Cloud project ID.

### Authentication: choose one

Recommended WIF variables:

- `GCP_WIF_PROVIDER`
- `GCP_SERVICE_ACCOUNT`

Fallback secret for first staging only:

- `GCP_SA_KEY` — complete Google service-account JSON key.

The deployment identity must be able to enable APIs, manage Artifact Registry, create/configure a Cloud Storage bucket and IAM bindings, create/use the `longocr-runtime` service account, and deploy Cloud Run. Use least privilege after the first staging deployment is working.

### Required application secret

- `LONGOCR_API_KEY` — long random bearer token used by `/v1/*` and `/mcp`.

### Optional variable

- `LONGOCR_GCS_BUCKET` — custom GCS bucket name. If omitted, the workflow uses `longocr-jobs-${GCP_PROJECT_ID}`.

## Trigger

1. Switch GitHub to branch `release/v0.2.0-preview.1`.
2. Open `release-assets/`.
3. Upload the reviewed RC with the exact filename `LongImageOCR-v0.2.0-preview.1.zip`.
4. Commit the upload to the release branch.

That push automatically starts **Deploy LongImageOCR Staging**.

After a run already exists, it can also be re-run from the Actions UI after fixing variables/secrets.

## What the workflow does

1. extracts the RC ZIP on an Ubuntu GitHub-hosted runner;
2. installs Python 3.11 dependencies and runs the release-gate test suite;
3. authenticates to Google Cloud with WIF, or `GCP_SA_KEY` fallback;
4. enables Cloud Run / Artifact Registry / Storage / IAM APIs;
5. creates the Artifact Registry repository if needed;
6. creates the dedicated `longocr-runtime` service account if needed;
7. creates the shared GCS job bucket and 1-day lifecycle rule;
8. grants the runtime service account object access to the bucket;
9. builds the Docker image on the GitHub runner;
10. starts the container locally on the runner and checks `/health`;
11. pushes the image to Artifact Registry;
12. deploys Cloud Run staging with 2 vCPU, 4 GiB RAM, concurrency 1, timeout 300 seconds, and min instances 0;
13. verifies live `/health` with `gcs_enabled=true`;
14. submits a synthetic long-image OCR request and performs a follow-up `job_id` request;
15. runs `package_release.py --mcp-url <real-service-url>/mcp`;
16. uploads the configured ChatGPT Plugin ZIP and Workspace Studio production manifest as a GitHub Actions artifact.

## Outputs

The completed workflow run publishes an artifact named:

`longimageocr-staging-<commit-sha>`

It contains:

- `LongImageOCR-ChatGPT-Plugin-v0.2.0-preview.1.zip`
- `appsscript.production.json`
- `cloud-run-url.txt`
- `mcp-url.txt`
- live health JSON
- live job-status JSON

Do not merge this release branch into `main` until the generated plugin and Workspace Studio manifest pass live ChatGPT and Drive Gemini smoke tests.
