import subprocess
import random
import string
import os

def push_dataflow_payload(bucket_name):
    # push via a dataflow script into a user-provided GCS bucket. Ask user to give access to the bucket  first.
    # Replace YOURBUCKETNAMEHERE with bucket_name
    with open("./base_dataflow_pipeline/wordcount.py", "r") as file:
        filedata = file.read()
    filedata = filedata.replace("YOURBUCKETNAMEHERE", bucket_name)
    with open("./base_dataflow_pipeline/wordcount-overwritten.py", "w") as file:
        file.write(filedata)

    run_gcloud_command_local("gsutil cp ./base_dataflow_pipeline/wordcount-overwritten.py gs://{}/wordcount.py".format(bucket_name), gsutil=True)


def push_startup_payload(bucket_name):
    # push via a startup script into a user-provided GCS bucket. Ask user to give access to the bucket  first.
    # Replace YOURBUCKETNAMEHERE with bucket_name
    with open("./utils/startup.sh", "r") as file:
        filedata = file.read()
    filedata = filedata.replace("YOURBUCKETNAMEHERE", bucket_name)
    with open("./utils/startup-overwritten.sh", "w") as file:
        file.write(filedata)

    run_gcloud_command_local("gsutil cp ./utils/startup-overwritten.sh gs://{}/startup.sh".format(bucket_name), gsutil=True)
    run_gcloud_command_local("gcloud services enable services.googleapis.com")


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

