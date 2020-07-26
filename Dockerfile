from python
run touch hi
run echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
run curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
run apt-get update && apt-get install -y google-cloud-sdk
copy requirements.txt .
run pip install -r requirements.txt
copy . .
cmd ["python", "-u", "main.py"]
