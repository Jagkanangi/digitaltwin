# main.tf
resource "google_project" "digital_twin_project" {
  # This is exactly like your justfile logic: root_domain + "-digital-twin"
  name       = "${var.root_domain}-project-digital-twin"
  project_id = "${var.root_domain}-digital-twin"
  
  org_id     = var.organization_id
}

# The list of APIs from your screenshot
variable "gcp_service_list" {
  type = list(string)
  default = [
    "compute.googleapis.com",              # Compute Engine API
    "cloudbuild.googleapis.com",           # Cloud Build API
    "run.googleapis.com",                 # Cloud Run Admin API
    "secretmanager.googleapis.com",        # Secret Manager API
    "artifactregistry.googleapis.com",    # Artifact Registry API
    "logging.googleapis.com",             # Cloud Logging API
    "cloudaicompanion.googleapis.com",    # Gemini for Google Cloud API
    "certificatemanager.googleapis.com",  # Certificate Manager API
    "pubsub.googleapis.com",              # Cloud Pub/Sub API
    "iam.googleapis.com",                 # Identity and Access Management (IAM) API
    "appoptimization.googleapis.com",     # App Optimize API
    "iamcredentials.googleapis.com",      # IAM Service Account Credentials API
    "serviceusage.googleapis.com",        # Service Usage API
    "storage.googleapis.com",              # Cloud Storage API
    "vpcaccess.googleapis.com",             # VPC Access API
    "servicenetworking.googleapis.com",     #vpc peerings
    "redis.googleapis.com"            # Memorystore for Redis API
  ]
}

# The Loop that enables them all
resource "google_project_service" "gcp_services" {
  for_each = toset(var.gcp_service_list)
  project  = "${var.root_domain}-digital-twin" # This uses your variable logic
  service  = each.key

  # Prevents accidental data loss if the API is removed from the list [cite: 2026-01-05]
  disable_on_destroy = false 
}

# 1. Create the 'Vault' for the GitHub Token
resource "google_secret_manager_secret" "github_token" {
  secret_id = "github-token"

  replication {
    auto {}
  }

  depends_on = [google_project_service.gcp_services]
}


############################################################
#CREATE ALL SECRETS MANUALLY BEFORE PROCEEDING ANY FURTHER
###########################################################


resource "google_compute_global_address" "external_ip" {
  name         = "${var.root_domain}-external-ip-address"
  depends_on = [google_project_service.gcp_services]
}

#Create a "Map" of your domains to keep things organized
locals {
  domains = {
    root         = "${var.root_domain}${var.tld}"
    www          = "${var.www_sub_domain}.${var.root_domain}${var.tld}"
    (var.sub_domain1)  = "${var.sub_domain1}.${var.root_domain}${var.tld}"
    (var.sub_domain2)  = "${var.sub_domain2}.${var.root_domain}${var.tld}"
  }
}

# 2. Use a loop to create the DNS Authorizations
resource "google_certificate_manager_dns_authorization" "dns_auth" {
  for_each = local.domains
  name        = "auth-${var.root_domain}-${each.key}" 
  domain      = each.value
  description = "DNS authorization for ${each.key} subdomain"
  
  # Ensure the Certificate Manager API is enabled first
  depends_on = [google_project_service.gcp_services]
}

resource "google_certificate_manager_certificate" "managed_cert" {
  name        = "${var.root_domain}-ca-certificates" # 
  description = "Managed certificate for all subdomains"

  managed {
    domains = [
      for domain in local.domains : domain
    ]
    dns_authorizations = [
      for auth in google_certificate_manager_dns_authorization.dns_auth : auth.id
    ]
  }

  depends_on = [google_project_service.gcp_services]
}

# --- 1. The 'Sensor' (Data Source) ---
# This looks up for project details so we can get the Project Number automatically to create chroma db and redis accounts.
data "google_project" "project" {
  project_id = "${var.root_domain}-digital-twin"
}

# --- 2. The 'New' Accounts (Resources) ---
# These are the ones you explicitly asked to create for Redis and Chroma.
resource "google_service_account" "custom_service_accounts" {
  for_each     = toset(["chromadb-sa", "redis-sa"])
  account_id   = each.key
  display_name = each.key == "chromadb-sa" ? "ChromaDB Service Account" : "Redis Persistence SA"
}

# --- 3. The 'Cloud Build' Roles ---
# Giving permissions to the default account Google created for builds.
resource "google_project_iam_member" "cloud_build_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
    "roles/artifactregistry.admin"
  ])
  project = data.google_project.project.project_id
  role    = each.key
  member  = "serviceAccount:${data.google_project.project.number}@cloudbuild.gserviceaccount.com"

  # Wait for APIs to be enabled so this account actually exists [cite: 2026-01-05]
  depends_on = [google_project_service.gcp_services]
}

# --- 4. The 'Compute' Roles ---
# Giving permissions to the default account that runs your Cloud Run containers.
resource "google_project_iam_member" "compute_roles" {
  for_each = toset([
    "roles/logging.logWriter",
    "roles/artifactregistry.writer",
    "roles/run.admin",
    "roles/iam.serviceAccountUser"
  ])
  project = data.google_project.project.project_id
  role    = each.key
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"

  depends_on = [google_project_service.gcp_services]
}

# Give the Cloud Build Service Agent permission to read your GitHub token
resource "google_secret_manager_secret_iam_member" "cloud_build_secret_reader" {
  secret_id = google_secret_manager_secret.github_token.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:service-${data.google_project.project.number}@gcp-sa-cloudbuild.iam.gserviceaccount.com"
}

# The Warehouse for all your Digital Twin images
resource "google_artifact_registry_repository" "digital_twin_registry" {
  location      = var.region
  # Using your variable for the ID
  repository_id = var.repo_name 
  description   = "Deployment artifact storage for UI and API"
  format        = "DOCKER"

  depends_on = [google_project_service.gcp_services]
}

# The "Handshake" between Google Cloud and GitHub
resource "google_cloudbuildv2_connection" "my_github_connection" {
  location = var.region
  name     = var.repo_connection_name

  github_config {
    # This is the numeric ID from your GitHub App installation
    app_installation_id = var.gcp_git_installation_id

    authorizer_credential {
      # We point directly to the Secret ID we created earlier
      oauth_token_secret_version = google_secret_manager_secret_version.github_token_version.id
    }
  }

  # Ensure the Cloud Build API is on first
  depends_on = [google_project_service.gcp_services]
}

# 1. Define the specific repositories you want to link
locals {
  github_repositories = {
    ui      = "https://github.com/${var.github_user}/${var.ui_repo_name}.git"
    service = "https://github.com/${var.github_user}/${var.service_repo_name}.git"
  }
}

# 2. Create the links in Google Cloud Build
resource "google_cloudbuildv2_repository" "my_repos" {
  for_each = local.github_repositories

  name              = "${var.repo_link_name}-${each.key}"
  parent_connection = google_cloudbuildv2_connection.my_github_connection.id
  remote_uri        = each.value

  # This ensures the connection is fully established before linking repos
  depends_on = [google_cloudbuildv2_connection.my_github_connection]
}

# 1. Define the specific repositories you want to link
locals {
  github_repositories = {
    ui      = "https://github.com/${var.github_user}/${var.ui_repo_name}.git"
    service = "https://github.com/${var.github_user}/${var.service_repo_name}.git"
  }
}

# 2. Create the links in Google Cloud Build
resource "google_cloudbuildv2_repository" "my_repos" {
  for_each = local.github_repositories

  name              = "${var.repo_link_name}-${each.key}"
  parent_connection = google_cloudbuildv2_connection.my_github_connection.id
  remote_uri        = each.value

  # This ensures the connection is fully established before linking repos
  depends_on = [google_cloudbuildv2_connection.my_github_connection]
}

# Trigger that reacts to GitHub pushes
resource "google_cloudbuild_trigger" "github_triggers" {
  for_each = google_cloudbuildv2_repository.my_repos # Loop through our linked repos

  name     = "${var.trigger_name}-${each.key}"
  location = var.region

  # Use the 2nd Gen Repository Connection
  repository_event_config {
    repository = each.value.id
    push {
      branch = "^main$"
    }
  }

  # Tell Google which file to look for in your code
  filename = "cloudbuild.yaml"

  # The Identity that will perform the build [cite: 2026-03-02]
  service_account = "projects/${data.google_project.project.project_id}/serviceAccounts/${data.google_project.project.number}-compute@developer.gserviceaccount.com"

  # Ensure the repositories are linked before creating the trigger
  depends_on = [google_cloudbuildv2_repository.my_repos]
}

# 1. The Network
resource "google_compute_network" "vpc_network" {
  name                    = "$(var.domain_name)-digital-twin-vpc"
  auto_create_subnetworks = false
}

# 2. The Subnet 
resource "google_compute_subnetwork" "vpc_subnet" {
  name          = "$(var.domain_name)-digital-twin-subnet"
  ip_cidr_range = "10.0.1.0/28" # Small range for internal traffic
  region        = var.region
  network       = google_compute_network.vpc_network.id
}

# 3. The Connector (The "Tunnel" for Cloud Run)
resource "google_vpc_access_connector" "connector" {
  name          = "$(var.domain_name)-run-vpc-connector"
  region        = var.region
  
  # This tells the tunnel which subnet to use
  subnet {
    name = google_compute_subnetwork.vpc_subnet.name
  }

  # We only need a small machine for this tunnel
  machine_type = "e2-micro"
}

# ============================================================
# 1. THE SERVICES (The "Invisible" API & The "Gateway" UI)
# ============================================================

# THE SERVICE (API) - Hidden from the public internet
resource "google_cloud_run_v2_service" "api_service" {
  name     = $(var.webservice_module_name)
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY" # The "Locked Door"

  template {
    # This connects the API to Redis/ChromaDB inside the VPC
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${data.google_project.project.project_id}/${var.repo_name}/${var.webservice_module_name}:latest"
    }
  }
}

# THE UI (Nginx) - Only accepts traffic from your Load Balancer
resource "google_cloud_run_v2_service" "ui_service" {
  name     = $(var.website_module_name)
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER" 

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${data.google_project.project.project_id}/${var.repo_name}/digital-twin-ui:latest"
      
      # Tell Nginx where the API lives
      env {
        name  = "SERVICE_URL"
        value = google_cloud_run_v2_service.api_service.uri
      }
    }
  }
}

# ============================================================
# 2. THE BRIDGE (Serverless NEG)
# ============================================================
# This tells the Global Load Balancer how to find UI Cloud Run

resource "google_compute_region_network_endpoint_group" "ui_neg" {
  name                  = "${var.root_domain}-digital-twin-ui-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  cloud_run {
    service = google_cloud_run_v2_service.ui_service.name
  }
}

# ============================================================
# 3. THE LOAD BALANCER (The Traffic Cop)
# ============================================================

# Create the Backend Service
resource "google_compute_backend_service" "ui_backend" {
  name                  = "${var.root_domain}-digital-twin-backend"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  protocol              = "HTTP"

  backend {
    group = google_compute_region_network_endpoint_group.ui_neg.id
  }
}

# Create the URL Map (Routes your domains to the backend)
resource "google_compute_url_map" "ui_url_map" {
  name            = "${var.root_domain}-digital-twin-url-map"
  default_service = google_compute_backend_service.ui_backend.id
}

# ============================================================
# 4. THE FRONT END (The HTTPS Door)
# ============================================================

# Target HTTPS Proxy (Links your SSL Certs to the URL Map)
resource "google_compute_target_https_proxy" "https_proxy" {
  name             = "${var.root_domain}-https-proxy"
  url_map          = google_compute_url_map.ui_url_map.id
  certificate_map  = google_certificate_manager_map.managed_cert.id
}

# Forwarding Rule (The actual Public IP that users hit)
resource "google_compute_global_forwarding_rule" "https_forwarding_rule" {
  name                  = "${var.root_domain}-https-forwarding-rule"
  target                = google_compute_target_https_proxy.https_proxy.id
  port_range            = "443"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  ip_address            = google_compute_global_address.external_ip.id 
}