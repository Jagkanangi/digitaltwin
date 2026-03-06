
[group('setup')]
@ollama:
    ollama pull nomic-embed-text

[group('run')]
@run:
    uv run gradio src/GradioUI.py


#install google cli if it is not there already
[group('google-cli-installation')]
install-google-cli:
    #!/usr/bin/env bash
    # Check if gcloud is already installed
    if command -v gcloud &> /dev/null; then
        echo "gcloud CLI is already installed. Skipping..."
        exit 0
    fi

    sudo apt-get update && sudo apt-get install -y apt-transport-https ca-certificates gnupg curl
    
    # Get the public key from google so linux will be happy to trust packages.cloud.google.com/apt when it calls update. Only add the key if it doesn't exist 
    if [ ! -f /usr/share/keyrings/cloud.google.gpg ]; then
        curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
    fi

    # Overwrite instead of Append (use tee without -a) to prevent duplicates
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list

    # Finally, update apt-get and install the gcloud CLI
    sudo apt-get update && sudo apt-get install -y google-cloud-cli




# Generate a unique project ID using a prefix and a UUID
# Note: GCP Project IDs must be lowercase and start with a letter.

website_module_name := "digital-twin-ui-website"
organization_id := shell(gcloud projects describe YOUR_PROJECT_ID --format="value(parent.id)")
project_id := "digital-twin"
project_name := "project_name"
PROJECT_NUMBER := shell("gcloud projects describe " + project_id + " --format='value(projectNumber)'")
region := "northamerica-northeast2"
backend_service_name := "digital-twin-backend" #this is not the webservice
NEG_name := "digital-twin-ui-neg"
url_map := "digital-twin-url-map"
ssl_certificates := "ca-certificates"
cert_map := "cert-map"
ip_address := "xxxx"
forwarding_rule := "digital-twin-lb"
https_proxy := "https-proxy"
repo_name := "my-profile-website"
github_user := "XXXX"
github_repo := "xxxx"
trigger_name := "twin-push-trigger"
repo_connection_name := "digital-twin-ui-github-connection"
repo_link_name  := "digital-twin-ui-link" # The name GCP uses for this link
#get this value from github. install from the marketpace https://github.com/marketplace/google-cloud-build. once installed you will see the id on the url
gcp_git_installation_id := "xxxxx"
chorma_bucket_name := "digital_twin_bucket"
chroma_db := "paste your create_url_map"
redis_bucket_name := "redis_bucket"
redis_service := "paste your url"
domain := "Your domain name"
subdomain := "www"
# Recipe to create a project with a unique ID
create-project:
    @echo "Creating project with ID: {{project_id}}"
    gcloud projects create {{project_id}} --organization={{organization_id}} --name={{project_name}}
    gcloud config set project {{project_id}}

[group('create_external_ip')] 
create_external_ip:
    gcloud compute addresses create external-ip-address \
        --network-tier=PREMIUM \
        --global
[group('create_certificates')]
create_dns: 
    #mutliple of these if you want subdomains
    gcloud certificate-manager dns-authorizations create auth-root --domain={{domain}}
    gcloud certificate-manager dns-authorizations create auth-www --domain={{subdomain}}.{{domain}}
[group('create_certificates')]
generate_CNAME_maps:
    gcloud certificate-manager dns-authorizations describe auth-root
    gcloud certificate-manager dns-authorizations describe auth-www
#important map the above values to the domain name service
[group('create_certificates')]
create_certificates:
    gcloud certificate-manager certificates create {{ssl_certificates}} \
        --domains="" \
        --dns-authorizations="auth-root,auth-www"
#create the map so load balancer can see it
[group('create_certificates')]
create_certificate_map:
    gcloud certificate-manager maps create {{cert_map}}
    # map entries for the map Repeat this for root, www and any other domain
    gcloud certificate-manager maps entries create www \
        --map={{cert_map}} \
        --hostname={{subdomain}}.{{domain}} \
        --certificates={{ssl_certificates}}
    gcloud certificate-manager maps entries create root \
        --map={{cert_map}} \
        --hostname={{domain}}" \
        --certificates={{ssl_certificates}}

# create auto ci/cd so the cloud run service can be create before creating neg
# enable appropriate apis for this
[group('ci_cd')]
enable_cicd_apis:
    gcloud services enable cloudbuild.googleapis.com \
                       run.googleapis.com \
                       containerregistry.googleapis.com \
                       artifactregistry.googleapis.com
[group('ci_cd')]
create_user_roles:
    @echo "Confirmed Project Number: {{PROJECT_NUMBER}}"
    # rights to read and write to a log
    gcloud projects add-iam-policy-binding {{project_id}} \
        --member="serviceAccount:{{PROJECT_NUMBER}}@cloudbuild.gserviceaccount.com" \
        --role="roles/logging.logWriter"
    # rights to build and deploy
    gcloud projects add-iam-policy-binding {{project_id}} \
        --member="serviceAccount:{{PROJECT_NUMBER}}@cloudbuild.gserviceaccount.com" \
        --role="roles/run.admin"
    # Permission to act as the runtime service account    
    gcloud projects add-iam-policy-binding {{project_id}} \
        --member="serviceAccount:{{PROJECT_NUMBER}}@cloudbuild.gserviceaccount.com" \
        --role="roles/iam.serviceAccountUser"
    # rights to push to aritifact registry    
    gcloud projects add-iam-policy-binding {{project_id}} \
        --member="serviceAccount:{{PROJECT_NUMBER}}@cloudbuild.gserviceaccount.com" \
        --role="roles/artifactregistry.admin"
    # rights to read passwords    
    gcloud secrets add-iam-policy-binding github-token \
        --member="serviceAccount:service-{{PROJECT_NUMBER}}@gcp-sa-cloudbuild.iam.gserviceaccount.com" \
        --role="roles/secretmanager.secretAccessor"
    gcloud projects add-iam-policy-binding {{project_id}} \
        --member="serviceAccount:{{PROJECT_NUMBER}}-compute@developer.gserviceaccount.com" \
        --role="roles/logging.logWriter" \
        --condition=None
    gcloud projects add-iam-policy-binding {{project_id}} \
        --member="serviceAccount:{{PROJECT_NUMBER}}-compute@developer.gserviceaccount.com" \
        --role="roles/artifactregistry.writer" \
        --condition=None
    # 1. Permission to manage the Cloud Run service
    gcloud projects add-iam-policy-binding {{project_id}} \
        --member="serviceAccount:{{PROJECT_NUMBER}}-compute@developer.gserviceaccount.com" \
        --role="roles/run.admin" \
        --condition=None

    # 2. Permission to 'act as' the identity that runs the container
    gcloud projects add-iam-policy-binding {{project_id}} \
        --member="serviceAccount:{{PROJECT_NUMBER}}-compute@developer.gserviceaccount.com" \
        --role="roles/iam.serviceAccountUser" \
        --condition=None

[group('ci_cd')]
create_repo:
    @echo "Creating Artifact Registry repository..."
    gcloud artifacts repositories create {{repo_name}} \
        --repository-format=docker \
        --location={{region}} \
        --description="Digital Twin Container Storage" \
        --project={{project_id}}
[group('ci_cd')]
create_git_authorization:
    # Create the secret "container"
    gcloud secrets create github-token --replication-policy="automatic"

    # Add your PAT as the version (It will prompt you for the value)
    echo -n "GET_GIT_CLASSIC_TOKEN_FROM_GITHUB_PROFILE_SETTINGS_DEVELOPER_SETTINGS_CLASSIC_TOKENS_AND_PASTE_HERE ACCESS NEEDED repo, read:user, admin:repo_hook" | gcloud secrets versions add github-token --data-file=-
[group('ci_cd')]
create_git_connection:
    gcloud builds connections create github {{repo_connection_name}} \
        --region={{region}} \
        --app-installation-id={{gcp_git_installation_id}} \
        --authorizer-token-secret-version=projects/{{project_id}}/secrets/github-token/versions/latest
link_repo:
    @echo "Linking GitHub repository to GCP..."
    gcloud builds repositories create {{repo_link_name}} \
        --remote-uri=https://github.com/{{github_user}}/{{github_repo}}.git \
        --connection={{repo_connection_name}} \
        --region={{region}} \
        --project={{project_id}}        
[group('ci_cd')]
create_trigger:
    @echo "Creating GitHub push trigger for {{github_repo}}..."
    
    gcloud builds triggers create github \
        --name="{{trigger_name}}" \
        --repository="projects/{{project_id}}/locations/{{region}}/connections/{{repo_connection_name}}/repositories/{{repo_link_name}}" \
        --branch-pattern="^main$" \
        --build-config="cloudbuild.yaml" \
        --region="{{region}}" \
        --project="{{project_id}}" \
        --service-account="projects/{{project_id}}/serviceAccounts/{{PROJECT_NUMBER}}-compute@developer.gserviceaccount.com"

# map domain to service
[group('service-domain-mapping')]
map_domains_to_service:
    gcloud beta run domain-mappings create \
        --service={{website_module_name}} \
        --domain={{subdomain}}.{{domain}}\
        --region={{region}}
    gcloud beta run domain-mappings create \
        --service={{website_module_name}} \
        --domain={{domain}}\
        --region={{region}}


[group('create_serverless_NEG')]
create_serverless_NEG:
    gcloud compute network-endpoint-groups create {{NEG_name}} \
        --region={{region}} \
        --network-endpoint-type=serverless \
        --cloud-run-service={{website_module_name}}

[group('create_backend_service')]
create_backend_service:
    # Create the manager and connect it to the backend service
    gcloud compute backend-services create {{backend_service_name}} \
        --load-balancing-scheme=EXTERNAL_MANAGED \
        --global && \
    gcloud compute backend-services add-backend {{backend_service_name}} \
        --global \
        --network-endpoint-group={{NEG_name}} \
        --network-endpoint-group-region={{region}}

[group('create_url_map')]
create_url_map:
    gcloud compute url-maps create {{url_map}} \
        --default-service={{backend_service_name}}

# Create the Target HTTPS Proxy to tie the Map and Cert together
create_http_proxy:
    gcloud compute target-https-proxies create {{https_proxy}} \
        --url-map={{url_map}} \
        --certificate-map={{cert_map}} \
        --global
# Create the Final Forwarding Rule (The Frontend)
create_forwarding_rules:
    gcloud compute forwarding-rules create {{forwarding_rule}} \
        --load-balancing-scheme=EXTERNAL_MANAGED \
        --network-tier=PREMIUM \
        --address={{ip_address}} \
        --global \
        --target-https-proxy={{https_proxy}} \
        --ports=443
#add bindings to open the ui to the internet

open_to_public:
    gcloud run services add-iam-policy-binding {{website_module_name}} \
        --region={{region}} \
        --member="allUsers" \
        --role="roles/run.invoker"
    gcloud run services update {{website_module_name}} \
        --ingress=all \
        --region={{region}}

create_chroma_setup:
    gcloud storage buckets create gs://{{chorma_bucket_name}} \
        --location={{region}} \
        --uniform-bucket-level-access
    gcloud iam service-accounts create chromadb-sa --display-name="ChromaDB Service Account"
    gcloud storage buckets add-iam-policy-binding gs://{{chorma_bucket_name}} \
        --member="serviceAccount:chromadb-sa@{{project_id}}.iam.gserviceaccount.com" \
        --role="roles/storage.objectAdmin"
    gcloud beta run deploy chromadb-service \
        --image=chromadb/chroma:latest \
        --platform=managed \
        --region={{region}} \
        --port=8000 \
        --set-env-vars=IS_PERSISTENT=TRUE,PERSIST_DIRECTORY=/data \
        --service-account=chromadb-sa@{{project_id}}.iam.gserviceaccount.com \
        --execution-environment=gen2 \
        --add-volume=name=chroma-storage,type=cloud-storage,bucket={{chorma_bucket_name}} \
        --add-volume-mount=volume=chroma-storage,mount-path=/data \
        --ingress=internal \
        --no-allow-unauthenticated
create_redis:
    # 1. Create the dedicated Service Account for Redis
    gcloud iam service-accounts create redis-sa \
        --display-name="Redis Persistence SA" \
        --project={{project_id}}

    # 2. Create the Single-Region Bucket
    gcloud storage buckets create gs://{{redis_bucket_name}} \
        --location={{region}} \
        --uniform-bucket-level-access \
        --project={{project_id}}

    # 3. Bind IAM Permissions (Granting SA access to the bucket)
    gcloud storage buckets add-iam-policy-binding gs://{{redis_bucket_name}} \
        --member="serviceAccount:redis-sa@{{project_id}}.iam.gserviceaccount.com" \
        --role="roles/storage.objectAdmin"
temp:
    # 4. Deploy the Redis Service
    gcloud beta run deploy redis-service \
        --image=redis:7-alpine \
        --region={{region}} \
        --port=6379 \
        --service-account=redis-sa@{{project_id}}.iam.gserviceaccount.com \
        --execution-environment=gen2 \
        --add-volume=name=redis-storage,type=cloud-storage,bucket={{redis_bucket_name}} \
        --add-volume-mount=volume=redis-storage,mount-path=/data \
        --ingress=internal \
        --no-allow-unauthenticated \
        --max-instances=1 \
        --set-env-vars=REDIS_ARGS="--appendonly yes --dir /data --maxmemory 512mb --maxmemory-policy allkeys-lru --protected-mode no" \
        --command="redis-server" \
        --args="--appendonly","yes","--dir","/data","--maxmemory","512mb","--maxmemory-policy","allkeys-lru","--protected-mode","no" \
        --project={{project_id}}
        