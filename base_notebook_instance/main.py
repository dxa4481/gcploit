import subprocess
import random
import io
import string
import json
import os
from urllib.request import Request, urlopen
from base64 import b64decode, b64encode

from utils import utils

def create_notebook_in_another_project(dest_project, dest_sa, instance_props, bucket_name):
    # Creates a Dataflow notebook in another project.
    utils.run_gcloud_command_local("gcloud config set project {}".format(dest_project))

    utils.push_startup_payload(bucket_name)

    succeeded = utils.run_gcloud_command_local("gcloud beta notebooks instances create {} --service-account {} --location=us-central1-a --vm-image-family ubuntu-2004-lts --vm-image-project ubuntu-os-cloud --post-startup-script=gs://{}/startup.sh --metadata startup-script-url=gs://{}/startup.sh".format(instance_props["name"], dest_sa, bucket_name, bucket_name))

    print("~~~~~~~~~~ {} ~~~~~~~~~~".format(succeeded))
    if not succeeded and succeeded != "0" and succeeded != 0:
        print("gcp vm provisioning failed")
        return False
    return instance_props

if __name__ == "__main__":
    module = __import__(__name__)
    with open(module.__file__) as f:
        current_cf = f.read()
