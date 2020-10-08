import requests
import argparse
import sys
import json
import subprocess
from time import sleep
import shlex

dangerous_permissions = [
    "dataproc.clusters.create",
    "composer.environments.create",
    "dataflow.jobs.create",
    "iam.serviceAccounts.setIamPolicy",
    "dataprep.projects.use",
    "deploymentmanager.deployments.create",
    "datafusion.instances.create",
    "iam.serviceAccounts.actAs",
    "iam.serviceAccounts.getAccessToken",
    "iam.serviceAccounts.getOpenIdToken",
    "iam.serviceAccounts.signBlob",
    "iam.serviceAccounts.signJwt",
    "iam.serviceAccounts.implicitDelegation",
    "resourcemanager.projects.setIamPolicy",
    "resourcemanager.folders.setIamPolicy",
    "resourcemanager.organizations.setIamPolicy",
    "resourcemanager.folders.setIamPolicy",
    "resourcemanager.projects.setIamPolicy",
]

def bfs_search(org, base_id):
    token = subprocess.check_output("gcloud auth print-access-token".split(" ")).decode("utf-8")
    token = token.strip()

    headers = {
        "Authorization": "Bearer {}".format(token),
        "content-type": "application/json",
        "x-http-method-override": "GET"
    }


    visited = []
    visited_projects = []
    info = {}
    queue = [base_id]
    while queue:
        service_account = queue.pop()
        visited.append(service_account)
        JSON_REQUEST={
          "analysisQuery": {
            "parent": org,
            "identitySelector": {
                "identity": "serviceAccount:{}".format(service_account)
            },
            "accessSelector": {
                "permissions": []
            }
          }
        }
# currently getting this error response from GCP
# we need to split up dangerous_permissions and run multiple requests
# {"error": {"code": 400, "message": "Some specified value(s) are invalid.", "status": "INVALID_ARGUMENT", "details": [{"@type": "type.googleapis.com/google.rpc.BadRequest", "fieldViolations": [{"field": "access_selector", "description": "In one request, the total number of roles and permissions should be equal or less than 10. If you have more than that, please split your request into multiple ones."}]}]}}
        perms_added = 0
        for dangerous_permission in dangerous_permissions:
            if len(JSON_REQUEST["analysisQuery"]["accessSelector"]["permissions"]) < 10 and perms_added < len(dangerous_permissions):
                JSON_REQUEST["analysisQuery"]["accessSelector"]["permissions"].append(dangerous_permission)
                perms_added += 1
            else:
                sleep(0.15)
                res = requests.post("https://cloudasset.googleapis.com/v1p4beta1/organizations/{}:analyzeIamPolicy".format(org), headers=headers, json=JSON_REQUEST)
                res.raise_for_status()
                results = res.json()
                json_formatted_str = json.dumps(results)
                JSON_REQUEST["analysisQuery"]["accessSelector"]["permissions"].clear()

                if "analysisResults" in results["mainAnalysis"]:
                    for result in results["mainAnalysis"]["analysisResults"]:
                        recipient = result["attachedResourceFullName"]
                        target = recipient.split("/")[-1]
                        if recipient.startswith("//cloudresourcemanager.googleapis.com/projects"):
                            if target not in visited_projects:
                                visited_projects.append(target)
                                command = "gcloud iam service-accounts list --format json --project {}".format(target)
                                sleep(0.05)
                                project_service_accounts = json.loads(subprocess.check_output(command.split(" ")).decode("utf-8"))
                                for project_service_account in project_service_accounts:
                                    sa_email = project_service_account["email"]
                                    if sa_email not in visited and sa_email not in queue:
                                        queue.append(sa_email)
                                        info[sa_email] = target
                                        print("Adding {} by means of {} with {}".format(sa_email, service_account, result["iamBinding"]["role"]))

                        elif recipient.startswith("//iam.googleapis.com/projects/"):
                            if target not in visited and target not in queue:
                                queue.append(target)
                                info[target] = recipient.split("/")[-3]
                                print("Adding {} by means of {} with {}".format(target, service_account, result["iamBinding"]["role"]))
 
    return visited, info

def visit(org_id, base_id):
    visited, info = bfs_search(org_id, base_id)

    print("\n\n~~~~~~~{} can move laterally to the following identities ~~~~~~~~~~~".format(base_id))
    for service_account in visited:
        if service_account != base_id:
            print("{} from project {}".format(service_account, info[service_account]))
    print("\n\n")
    return

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='bfs tool for GCP service account exploitation.')
    parser.add_argument('--source', dest="source",
                    help='The starting point for your bfs search')
    parser.add_argument('--org_id', dest="org",
                    help='Your org ID')
    parser.add_argument('--auto', action="store_true",
                    help='Automatically step through every project default compute service account in the organization')

    args = parser.parse_args()
    if not args.source and not args.auto:
        print("Need the starting point --source <serviceAccountEmail>")
        sys.exit()
    elif not args.org:
        print("Need the org ID --org_id <org_id>")
        sys.exit()

    org_id = args.org
    if args.source:
        base_id = args.source
        visit(org_id, base_id)
    elif args.auto:
        command = 'gcloud projects list --format "value(projectNumber)"'
        process = subprocess.run(shlex.split(command), capture_output=True, text=True)
        process.check_returncode()
        project_list = process.stdout.splitlines()
        for number in project_list:
            base_id = number + "-compute@developer.gserviceaccount.com"
            visit(org_id, base_id)
            sleep(20)
