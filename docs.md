# docs

# Getting started
On first setup

# JSON
## Expected JSON output for the readings
{'title': '', 'text': ''}
## Expected JSON output for the questions
{'questions': [{'question': '', 'answers': [], 'correct': []}, ]}
### Example
{'questions': [{'question': 'What did Tim find while playing in the park?', 'answers': ['A pair of colorful shoes', 'A shiny pair of headphones', 'A red ball'], 'correct': [False, True, False]}, 
{'question': 'Do you think Tim will continue using his magical headphones for more adventures? Why?', 'answers': [], 'correct': []}]}
# Upload to cloud run
pip freeze > requirements.txt
### Must run when you start a new terminal instance
PROJECT_ID=$(gcloud config get-value core/project)
REGION=us-central1
SERVICE_ACCOUNT=$(gcloud iam service-accounts list \
    --filter cloudrun-serviceaccount --format "value(email)")
ARTIFACT_REGISTRY=${REGION}-docker.pkg.dev/${PROJECT_ID}/containers
## Steps
### Create Service account 
gcloud iam service-accounts create cloudrun-serviceaccount
gcloud artifacts repositories create containers --repository-format docker --location $REGION
### Create relational database
gcloud sql instances create youcademyrelational --project $PROJECT_ID \
  --database-version POSTGRES_14 --tier db-f1-micro --region $REGION
gcloud sql databases create youcademydb --instance youcademyrelational
### Create password and user
DJPASS="$(cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9' | fold -w 30 | head -n 1)"

gcloud sql users create djuser --instance youcademyrelational --password $DJPASS
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member serviceAccount:${SERVICE_ACCOUNT} \
    --role roles/cloudsql.client
### Create unstructured static database
GS_BUCKET_NAME=${PROJECT_ID}-media
gcloud storage buckets create gs://${GS_BUCKET_NAME} --location ${REGION} 

gcloud storage buckets add-iam-policy-binding gs://${GS_BUCKET_NAME} \
    --member serviceAccount:${SERVICE_ACCOUNT} \
    --role roles/storage.admin
### Create.env file for database secrets 
echo DATABASE_URL=\"postgres://djuser:${DJPASS}@//cloudsql/${PROJECT_ID}:${REGION}:youcademyrelational/youcademydb\" > .env

echo GS_BUCKET_NAME=\"${GS_BUCKET_NAME}\" >> .env

echo SECRET_KEY=\"$(cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9' | fold -w 50 | head -n 1)\" >> .env

echo DEBUG=False >> .env

gcloud secrets create application_settings --data-file .env

gcloud secrets add-iam-policy-binding application_settings \
  --member serviceAccount:${SERVICE_ACCOUNT} --role roles/secretmanager.secretAccessor

gcloud secrets versions list application_settings

rm .env
### Helpful git commands
Archive branch and delete:
git tag archive/<branchname> <branchname>
git branch -d <branchname>
Push to github:
git push origin archive/<branchname>
git push origin --delete <branchname>
### Unarchive the branch
git checkout -b <branchname> archive/<branchname>