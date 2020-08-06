import requests
import argparse
import sys
import json
import subprocess

dangerous_permissions = [
    "dataproc.clusters.create",
    "composer.environments.create",
    "dataflow.jobs.create",
    "iam.serviceAccounts.setIamPolicy",
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
        for dangerous_permission in dangerous_permissions:
            JSON_REQUEST["analysisQuery"]["accessSelector"]["permissions"].append(dangerous_permission)
        res = requests.post("https://cloudasset.googleapis.com/v1p4beta1/organizations/{}:analyzeIamPolicy".format(org), headers=headers, json=JSON_REQUEST)
        results = res.json()
        if "analysisResults" in results["mainAnalysis"]:
            for result in results["mainAnalysis"]["analysisResults"]:
                recipient = result["attachedResourceFullName"]
                target = recipient.split("/")[-1]
                if recipient.startswith("//cloudresourcemanager.googleapis.com/projects"):
                    if target not in visited_projects:
                        visited_projects.append(target)
                        command = "gcloud iam service-accounts list --format json --project {}".format(target)
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

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='bfs tool for GCP service account exploitation.')
    parser.add_argument('--source', dest="source",
                    help='The starting point for your bfs search')
    parser.add_argument('--org_id', dest="org",
                    help='Your org ID')

    args = parser.parse_args()
    if not args.source:
        print("Need the starting point --start <serviceAccountEmail>")
        sys.exit()
    elif not args.org:
        print("Need the org ID --org_id <org_id>")
        sys.exit()

    base_id = args.source
    org_id = args.org
    visited, info = bfs_search(org_id, base_id)

    print("\n\n~~~~~~~{} can move laterally to the following identities ~~~~~~~~~~~".format(base_id))
    for service_account in visited:
        if service_account != base_id:
            print("{} from project {}".format(service_account, info[service_account]))
