import json
import string
import random

bad_roles = [
    "Dataproc Editor",
    "Dataproc Administrator",
    "Composer Administrator",
    "Dataflow Admin",
    "Dataflow Developer",
    "Service Account User",
    "Service Account Admin",
    "Service Account Token Creator"
]
roles = [
    "Storage admin",
    "Viewer",
    "Storage viewer",
    "Big Query Admin",
    "Compute Admin",
    "GKE Admin",
    "PubSub Admin",
    "Cloud KMS Admin",
    "Cloud Scheduler Admin",
    "Cloud SQL Admin",
    "Cloud SQL Client",
    "Firebase Admin",
    "Firebase Develop Viewer",
    "Logs Writer",
    "Logging Admin"
] + bad_roles



def randomString(stringLength=8):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))
"""
//cloudresourcemanager.googleapis.com/projects/49141858526
creating fake graph
average number of SA in popular project = 20
average number of cross project bindings in popular project = 50
average number of popular projects 1 in 3
28% chance of x project binding
"""
projects = {}
popular_projects = {}
unpopular_projects = {}
for i in range(100):
    project = {"service_accounts":[]}
    if random.randint(0,3) != 3:
        project["popular"] = False
        if random.randint(0,2) == 1:
            project["num_service_accounts"] = 0
        else:
            project["num_service_accounts"] = random.randint(0,2)
        projects[i] = project
        unpopular_projects[i] = project
    else:
        project["popular"] = True
        project["num_service_accounts"] = random.randint(0,40)
        projects[i] = project
        popular_projects[i] = project

for project in projects:
    for i in range(projects[project]["num_service_accounts"]):
        service_account = {"name": randomString()}
        if random.randint(0,100) > 28:
            service_account["binding"] = {"project": project, "role": random.choice(roles)}
        else:
            if random.randint(0,20) == 5:
                service_account["binding"] = {"project": random.choice(unpopular_projects.keys()), "role": random.choice(roles)}
            else:
                service_account["binding"] = {"project": random.choice(popular_projects.keys()), "role": random.choice(roles)}
        projects[project]["service_accounts"].append(service_account)
nodes = []
for project in projects:
    nodes.append({"data": {"type": "project", "id": project}})
    for serviceAccount in projects[project]["service_accounts"]:
        nodes.append({"data": {"type": "serviceAccount", "id": "{}@{}.iam.gserviceaccount.com".format(serviceAccount["name"], project)}})
edges = []
innocent_edges = []
for project in projects:
    for serviceAccount in projects[project]["service_accounts"]:
        sa_email = "{}@{}.iam.gserviceaccount.com".format(serviceAccount["name"], project)
        edges.append({"data": {"id": "serviceAccount:{}/contains".format(sa_email), "label": "contains", "source": project, "target": sa_email}})
        if serviceAccount["binding"]["role"] in bad_roles:
            edges.append({"data": {"id": "serviceAccount:{}/binding".format(sa_email), "label": serviceAccount["binding"]["role"], "source": sa_email, "target": serviceAccount["binding"]["project"]}})
        else:
            innocent_edges.append({"data": {"id": "serviceAccount:{}/binding".format(sa_email), "label": serviceAccount["binding"]["role"], "source": sa_email, "target": serviceAccount["binding"]["project"]}})
with open("animated-bfs/nodes.json", "w+") as f:
    f.write(json.dumps(nodes, indent=4))

with open("animated-bfs/edges.json", "w+") as f:
    f.write(json.dumps(edges, indent=4))

with open("animated-bfs/innocent_edges.json", "w+") as f:
    f.write(json.dumps(innocent_edges, indent=4))


