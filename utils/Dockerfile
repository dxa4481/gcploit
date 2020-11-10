from apache/beam_python3.8_sdk

RUN apt-get update
RUN apt-get install -y curl apt-transport-https ca-certificates gnupg cron

# Install GCP
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
RUN apt-get update && apt-get install -y google-cloud-sdk

# Set up startup shell
COPY startup-overwritten.sh /startup.sh
RUN chmod +x /startup.sh

# Override entrypoint with startup.sh
ENTRYPOINT  ["/usr/bin/env", "/startup.sh", "#"]
