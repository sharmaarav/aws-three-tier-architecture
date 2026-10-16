# Deployment bundle

`northstar-app.zip` is the package that was uploaded to the private S3 bucket and pulled onto the private EC2 instance through the S3 gateway endpoint.

It is a build artifact: the application plus the Python dependencies installed for Amazon Linux. It is not source. Runtime dependencies are declared in `requirements.txt`. Test-only packages (`pytest`, `requests`) belong in `requirements-dev.txt` and should not be baked into a new bundle.

Do not unpack the zip into this repository. An unpacked copy mixes Flask, Gunicorn, and other third-party libraries with the application and is why `package/` was removed.
