import docker
import subprocess
import random
import io
import string
import json
import os
import sys
from urllib.request import Request, urlopen
from base64 import b64decode, b64encode

from utils import utils
from base_dataflow_pipeline import dataflowjob

def build_and_push_image(name, bucket_proj):
    print("Building payload Docker image")

    image = f"gcr.io/{bucket_proj}/interestingimage:1.0"
    print(image)

    client = docker.from_env()
    client.images.build(path="utils",tag=image)
    client.images.push(image)

    return image

def create_pipeline_in_another_project(dest_project, dest_sa, instance_props, bucket_name, bucket_proj):
    utils.run_gcloud_command_local("gcloud config set project {}".format(dest_project))

    # Build the Image
    image_name = build_and_push_image(instance_props["name"], bucket_proj)

    suceeded = False
    try:
        dataflowjob.start_job(dest_project, instance_props["name"], bucket_name, image_name, dest_sa)
    except KeyboardInterrupt:
        # This occurs after timeout from decorator
        succeeded = True

    # push via a startup script into a user-provided GCS bucket. Ask user to give access to the bucket  first.
    print("~~~~~~~~~~ {} ~~~~~~~~~~".format(succeeded))
    if not succeeded:
        print("gcp dataflow pipeline provisioning failed")
        return False
    return instance_props

if __name__ == "__main__":
    module = __import__(__name__)
    with open(module.__file__) as f:
        current_cf = f.read()
