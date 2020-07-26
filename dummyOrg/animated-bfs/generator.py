import json


with open("iam2.json", "r") as f:
    roles = json.loads(f.read())


nodes = []
SAs = set()
projects = set()
for role in roles:
    for member in role["members"]:
        SAs.add(member)

for identity in SAs:
    if identity.endswith("@google.com"):
        nodes.append({"data": {"id": identity, "type": "userAccount"}})
    else:
        nodes.append({"data": {"id": identity, "type": "serviceAccount"}})


edges = []
for role in roles:
    for member in role["members"]:
        if member.endswith(".iam.gserviceaccount.com") and not member.startswith("serviceAccount:service-"):
            project = member.split("@")[1][:-24]
            projects.add(project)
            edges.append({ "data": { "id": member + project + "contains", "weight": 3, "source": project, "target": member, "label": "contains"} })
        elif member.endswith("-compute@developer.gserviceaccount.com"):
            project = member.split("serviceAccount:")[1][:-38]
            if project == "363997316495":
                edges.append({ "data": { "id": member + "ml-pipeline-test" + "contains", "weight": 3, "source": "ml-pipeline-test", "target": member, "label": "contains"} })
            else:
                edges.append({ "data": { "id": member + project + "contains", "weight": 3, "source": project, "target": member, "label": "contains"} })
                projects.add(project)

for project in projects:
    nodes.append({"data": {"id": project, "type": "project"}})


for role in roles:
     for member in role["members"]:
        edges.append({ "data": { "id": member+"ml-pipeline-test"+role["role"], "weight": 3, "source": member, "target": "ml-pipeline-test", "label": role["role"] } })


with open("edges.json", "w+") as f:
    f.write(json.dumps(edges))


with open("nodes.json", "w+") as f:
    f.write(json.dumps(nodes))
