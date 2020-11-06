import docker
import subprocess
import random
import io
import string
import json
import os
from urllib.request import Request, urlopen
from base64 import b64decode, b64encode

from utils import utils
from base_dataflow_pipeline import dataflowjob

def build_and_push_image(name, bucket_proj):
    print("Building payload Docker image")

    image = f"gcr.io/{bucket_proj}/{name}:1.0"

    client = docker.from_env()
    client.images.build(fileobj="base_dataflow_pipeline/Dockerfile",tag=image)
    client.images.push(image)

    return image

def create_pipeline_in_another_project(dest_project, dest_sa, instance_props, bucket_name, bucket_proj):
    utils.run_gcloud_command_local("gcloud config set project {}".format(dest_project))

    # Build the Image
    image_name = build_and_push_image(bucket_proj)
    dataflowjob.start_job(dest_project, instance_props["name"], bucket_name, image)

    # push via a startup script into a user-provided GCS bucket. Ask user to give access to the bucket  first.
    succeeded = utils.run_gcloud_command_local("gcloud dataflow jobs run {} --service-account-email {} --worker-zone=us-central1-a --parameters=[output={},runner='DataflowRunner',project={}]".format(instance_props["name"], dest_sa, bucket_name, dest_project))
    print("~~~~~~~~~~ {} ~~~~~~~~~~".format(succeeded))
    if not succeeded and succeeded != "0" and succeeded != 0:
        print("gcp dataflow pipeline provisioning failed")
        return False
    return instance_props

if __name__ == "__main__":
    module = __import__(__name__)
    with open(module.__file__) as f:
        current_cf = f.read()
