# gcploit

This repo has the code for the gcploit exploit framework, the BFS search tool meant for defensive threat models, a mock org simulator, as well as stack driver queries that profile the gcploit tool.


### BFS Search

To start you'll need the `cloudasset.assets.analyzeIamPolicy` permission at the organization level to use this tool.

Next do a `gcloud auth login` an complete the flow.

Finally run the tool `python bfs.py --org_id <orgId> --source <serviceAccountEmail>`

This will print the results of the BFS from your starting service account inside your org

Note bindings that come from other orgs won't be included here

### Mock Graph

To generate a mock graph, from the dummyOrg directory, run `python mockgraph.py` and copy `nodes.json` `edges.json` and `innocent_edges.json` into `animated-bfs` and then serve the content in the `animated-bfs` directory with `python -m http.server`

### Gcploit

Gcploit is a proof of concept, as-is framework for exploiting GCP. It includes some (not all) of the exploits we talked about in our talk.

These include:

    actAs
    dataproc

As of this moment, we don't have the following exploits implmented yet:
    
    tokenCreator
    dataflow
    composer
    compute admin
    dataprep
    google managed service account privesc (ie cloudbuild)
    datafusion
    cloudbuild
    actAs with VM's instead of GCF

To use the tool, docker is required.

First create an alias for the tool:

To mount in a base identity, authenticate to the base identity, and then pass in your gcloud credentials to the tool. Your credentials are typically found in $HOME/.config, so below is an example alias

    alias gcploit="docker run -v $(pwd)/db:/db -v $HOME/.config:/root/.config -it --rm dxa4481/gcploit python main.py"

Now you should be able to run:

    gcploit --list

If everything goes well you'll see no output

now you can try an exploit out:

    gcploit --exploit actas --project <project_name> --target_sa all

This exploit requires the base identity have `actAs` and `functionCreator` on the target project. In the future support for this without the `functionCreator` permission may be added (ie `computeAdmin` instead to use VM's instead of Functions)


Now if you run `gcloud --list` if all went well you should see a bunch of new service accounts you took control of through actAs

To interact with one of these try:

    gcploit --gcloud "projects list" --source <8charname>

now you can add the --source flag to your exploits and try something like

    gcploit --exploit actas --project <new_project_name> --source <8charname> --target_sa all

#### The use of a Proxy

Note often times oauth creds are all we get from these exploits, not json creds. To use these we spin up a proxy service in the function and live replace the oauth creds on outbound requests. This was done in a hacky way, and as a result it involves setting a proxy variable and unsetting a proxy variable in your .config. If the tool errors out or is killed mid command it's possible these may persist, and to clean it up you can run:

    gcloud config unset proxy/port
    gcloud config unset proxy/type
    gcloud config unset proxy/address
    gcloud config unset core/custom_ca_certs_file

#### Stack Driver Queries

The following Stack Driver query should give you insight into if this tool is being used against you in your environment:

```text    
protoPayload.request.function.timeout="539s"
```

The following examples demonstrate how to query logs using the gcloud CLI tool. 
https://cloud.google.com/sdk/gcloud/reference/logging/read

Query logs across an organization:
```bash 
gcloud logging read $STACK_DRIVER_FILTER --organization=$ORGANIZATION_ID --format json
```

Query logs in a specific folder: 
```bash 
gcloud logging read $STACK_DRIVER_FILTER --folder=$FOLDER_ID --format json
```

Query logs in a specific project:
```bash 
gcloud logging read $STACK_DRIVER_FILTER --project=$PROJECT_ID --format json
```
