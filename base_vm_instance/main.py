import subprocess
import random
import io
import string
import json
import os
from urllib.request import Request, urlopen
from base64 import b64decode, b64encode

def run_gcloud_command_local(command, gsutil=False):
    trigger = "gcloud"
    if gsutil:
        trigger = "gsutil"

    if command.split(" ")[0] != trigger:
        command = trigger + " " + command
    print("Running command:")
    print(command)
    try:
        cmd_output = subprocess.check_output(command.split(" "), stderr=subprocess.STDOUT)
        return cmd_output.decode("utf-8").rstrip()
    except subprocess.CalledProcessError as E:
        print("error code", E, E.output)
        return False

def run_os_command_local(command):
    return os.system(command)

def random_name(stringLength=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))

def create_vm_in_another_project(dest_project, dest_sa, instance_props, bucket_name):
    run_gcloud_command_local("gcloud config set project {}".format(dest_project))

    # Replace YOURBUCKETNAMEHERE with bucket_name
    with open("./base_vm_instance/startup.sh", "r") as file:
        filedata = file.read()
    filedata = filedata.replace("YOURBUCKETNAMEHERE", bucket_name)
    with open("./base_vm_instance/startup.sh", "w") as file:
        file.write(filedata)

    run_gcloud_command_local("gsutil cp ./base_vm_instance/startup.sh gs://{}".format(bucket_name), gsutil=True)
    run_gcloud_command_local("gcloud services enable services.googleapis.com")

    # push via a startup script into a user-provided GCS bucket. Ask user to give access to the bucket  first.
    succeeded = run_gcloud_command_local("gcloud compute instances create {} --service-account {} --scopes=cloud-platform --zone=us-central1-a --image-family ubuntu-2004-lts --image-project ubuntu-os-cloud --metadata startup-script-url=gs://{}/startup.sh".format(instance_props["name"], dest_sa, bucket_name))
    print("~~~~~~~~~~ {} ~~~~~~~~~~".format(succeeded))
    if not succeeded and succeeded != "0" and succeeded != 0:
        print("gcp vm provisioning failed")
        return False
    return instance_props

if __name__ == "__main__":
    module = __import__(__name__)
    with open(module.__file__) as f:
        current_cf = f.read()
