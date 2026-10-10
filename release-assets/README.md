# Staging release asset

Upload the reviewed release candidate here with the exact name:

`LongImageOCR-v0.2.0-preview.1.zip`

A push of that file on branch `release/v0.2.0-preview.1` triggers `.github/workflows/deploy-staging.yml`.

The workflow extracts the ZIP on the GitHub-hosted runner, installs dependencies, runs the full release-gate suite, builds and smoke-tests the Docker image, deploys Cloud Run staging, performs live health/OCR checks, and produces the configured ChatGPT plugin ZIP plus Workspace Studio production manifest as a GitHub Actions artifact.

Do not commit API keys, Google service-account JSON, or other credentials here. Configure them as GitHub Environment/Repository Secrets instead.
