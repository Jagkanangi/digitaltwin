###############################################################
# main.tf — Digital Twin Infrastructure (Teaching Version)
#
# This file builds a complete Google Cloud architecture using
# Terraform. It is written for BEGINNERS and explains both:
#   1. What Terraform is doing
#   2. Why each Google Cloud resource is needed
#
# Architecture Summary:
#   - Creates a new GCP project
#   - Enables required APIs
#   - Builds a private VPC network
#   - Adds a Serverless VPC Connector
#   - Deploys Redis (private)
#   - Deploys ChromaDB (private)
#   - Deploys API (internal-only Cloud Run)
#   - Deploys UI (public via HTTPS Load Balancer)
#   - Creates SSL certificates for multiple domains
#   - Creates a global HTTPS load balancer
#   - Integrates GitHub → Cloud Build → Cloud Run CI/CD
#   - Sets IAM permissions for service accounts
###############################################################


###############################################################
# 1. PROJECT SETUP 
# The What: 
# Terraform needs a GCP project to place all resources into.
# This block CREATES a brand new project.
# The Why:
# We want to keep all our digital twin resources organized in a single project.
# It also allows us to set up billing and permissions cleanly. 
# Without a project gcp will not know where to put resources or how to charge for them.
###############################################################

resource "google_project" "digital_twin_project" {
  name            = "${var.my_org_name}-project-digital-twin"
  project_id      = "${var.my_org_name}-digital-twin"
  org_id          = var.organization_id
  billing_account = var.billing_account_id
}

# The What:
# Terraform needs to know which APIs to enable.
# GCP services are disabled by default for security reasons.
# The Why:
# Every resource we create depends on specific APIs being enabled. For example, Cloud Run needs the "run.googleapis.com" API. 
# Enabling only what we need reduces our attack surface and prevents accidental usage of services that could incur costs or security risks.
# Enabling only the APIs we need reduces our attack surface and prevents accidental usage.
# These are the Google Cloud APIs that Terraform must enable
# before it can create the resources in this architecture.
# Each API below is required by at least one resource in main.tf.

variable "gcp_service_list" {
  type = list(string)
  default = [
    # Compute Engine — required for VPC, subnets, NAT, and firewall rules
    "compute.googleapis.com",

    # Cloud Build — used for CI/CD pipelines triggered by GitHub
    "cloudbuild.googleapis.com",

    # Cloud Run — used to deploy the API, UI, and ChromaDB services
    "run.googleapis.com",

    # Secret Manager — stores the GitHub token for Cloud Build authentication
    "secretmanager.googleapis.com",

    # Artifact Registry — stores Docker images for Cloud Run deployments
    "artifactregistry.googleapis.com",

    # Cloud Logging — collects logs from Cloud Run, NAT, and other services
    "logging.googleapis.com",

    # Certificate Manager — issues SSL certificates for your domains
    "certificatemanager.googleapis.com",

    # IAM — required for service accounts and IAM role bindings
    "iam.googleapis.com",

    # Storage — required for creating Cloud Storage buckets
    "storage.googleapis.com",

    # Serverless VPC Access — required for the VPC connector used by Cloud Run
    "vpcaccess.googleapis.com",

    # Service Networking — required for Private Service Access (Redis)
    "servicenetworking.googleapis.com",

    # Memorystore for Redis — required to create the Redis instance
    "redis.googleapis.com"
  ]
}
# Enable all required APIs
# This loop iterates over the list of APIs that we said we need and actually enables each one for the project.
resource "google_project_service" "gcp_services" {
  for_each           = toset(var.gcp_service_list)
  project            = google_project.digital_twin_project.project_id
  service            = each.key
  disable_on_destroy = false
}

# The What: 
# Fetch project metadata (like project number)
# The Why:
# We won't know the project number until after the project is created. This data source allows us to get that information.
# Note that we used data instead of resource to make the distinction that we are not creating a resource 
# but rather fetching existing information about the project we just created.
# 
data "google_project" "project" {
  project_id = google_project.digital_twin_project.project_id
  depends_on = [google_project_service.gcp_services]
}


###############################################################
# 2. NETWORKING — VPC, SUBNET, NAT, VPC CONNECTOR
# The What:
# This creates the private network where internal services run.
# Cloud Run cannot reach Redis or ChromaDB without this network.
# The Why:
# A VPC (Virtual Private Cloud) is a private network in Google Cloud. It allows us to run services that are not exposed to the public internet. 
# This is crucial for security, especially for databases like Redis and ChromaDB that should not be publicly accessible. 
# 
# The Serverless VPC Connector allows our Cloud Run services to communicate with resources inside the VPC, such as Redis and ChromaDB.
# The VPC network is the building and the VPC Connector is the keycard that allows Cloud Run services to enter the building and talk to the private services.
# 
# The subnet is a specific floor of the building with its own private IP range. Each floor can be considered as a department with its own responsibilities and security measures. 
# Example could be that the first floor (subnet) is for databases, the second floor is for internal services, and the third floor is for public-facing services.
# Or you could have one floor for development, one for staging, and one for production. The subnet allows us to organize and segment our resources within the VPC.
# 
# The NAT gateway is like a secure exit door for our private network. It allows resources inside to access the internet for updates or external API calls without. Our building 
# only has an entry for authorized personnel (Cloud Run services with VPC access) but we need an exit so we can access other resources such as external APIs. 
# By having this exit door (NAT)  we can keep our building (VPC) secure and private while still allowing necessary outbound communication without exposing our internal services to the internet.
# 
# VPC peering to allow our VPC to communicate with Google-managed services like Redis consider this as a pathway connecting 2 buildings. 
# The second building knows that anyone coming from our building through this pathway is trustworthy and are coming from our building.
# We use the vpc connector for our services like ChromaDB or the UI to talk to our webservice
# but we use vpc peering to allow our VPC to talk to the Google-managed Redis service since it also lives in a private network.
###############################################################

# The private network (the building)
resource "google_compute_network" "vpc_network" {
  name                    = "${var.my_org_name}-digital-twin-vpc"
  auto_create_subnetworks = false   # Beginners: we want full control
}

# A subnet inside the VPC (the floor of the building) The room numbers in this floor will be 10.0.1.x
resource "google_compute_subnetwork" "vpc_subnet" {
  name          = "${var.my_org_name}-digital-twin-subnet"
  ip_cidr_range = "10.0.1.0/24"     # Private IP range
  region        = var.region
  network       = google_compute_network.vpc_network.id
}

# Serverless VPC Connector (the keycard that allows Cloud Run to access the building)
# This allows Cloud Run to talk to Redis + ChromaDB privately.
resource "google_vpc_access_connector" "connector" {
  name   = "${var.my_org_name}-run-vpc-connector"
  region = var.region

  subnet {
    name = google_compute_subnetwork.vpc_subnet.name
  }

  machine_type = "e2-micro"         # Cheapest option
}

# Private Service Access (required for Redis) The tunnel we build
resource "google_compute_global_address" "google_service_range" {
  name          = "google-managed-services-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc_network.id
}

# we connect the tunnel to the google managed service building.
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.google_service_range.name]
}

# NAT Gateway — allows private services to reach the internet
resource "google_compute_address" "nat_ip" {
  name   = "${var.my_org_name}-nat-ip"
  region = var.region
}

# Why do we need a router? We need a router to manage the NAT gateway. 
# The router is like the traffic controller that directs outbound traffic from our private network to the internet through the NAT gateway. 
# It connects to an LLM or a payment processor via the

resource "google_compute_router" "router" {
  name    = "${var.my_org_name}-router"
  region  = var.region
  network = google_compute_network.vpc_network.id
}

# We create our NAT gateway and attach it to the router. This allows resources in our private network to access the internet securely without exposing them to inbound traffic.
resource "google_compute_router_nat" "nat" {
  name                               = "${var.my_org_name}-nat-gateway"
  router                             = google_compute_router.router.name
  region                             = var.region
  nat_ip_allocate_option             = "MANUAL_ONLY"
  nat_ips                            = [google_compute_address.nat_ip.self_link]
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}


###############################################################
# 3. DATABASE LAYER — REDIS + CHROMADB
#
# Redis = fast in-memory cache
# ChromaDB = vector database for embeddings
#
# Both run privately inside the VPC. The redis is Google-managed and the ChromaDB is self-hosted on Cloud Run.
###############################################################

resource "google_redis_instance" "cache" {
  name               = "digital-twin-redis"
  tier               = "BASIC"
  memory_size_gb     = 1
  region             = var.region
  authorized_network = google_compute_network.vpc_network.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"
}

resource "google_cloud_run_v2_service" "chromadb" {
  name     = "chromadb-service"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"   # Not public

  template {
    vpc_access {
      connector = google_vpc_access_connector.connector.id 
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "mirror.gcr.io/chromadb/chroma:latest"
      ports { container_port = 8000 }
    }
  }
}

# Allow Cloud Run → Redis traffic
resource "google_compute_firewall" "allow_redis" {
  name    = "allow-cloud-run-to-redis"
  network = google_compute_network.vpc_network.name

  allow {
    protocol = "tcp"
    ports    = ["6379"]
  }

  source_ranges = ["10.0.1.0/24"]
}


###############################################################
# The what:
# 4. ARTIFACT STORAGE — DOCKER REGISTRY + BUCKETS
# The why:
# This is the image repository for our Cloud Run services. When we deploy our API and UI, Cloud Build will build Docker images and push them here.
# Cloud Run will then pull the images from this registry to create and run our services. 
# Buckets are used to store any files or data we want to keep. 
# We 2 buckets one to to store chromadb data and another to store any files that we want to chunk and store in chromadb.
###############################################################

resource "google_artifact_registry_repository" "digital_twin_registry" {
  location      = var.region
  repository_id = var.repo_name
  format        = "DOCKER"
}

resource "google_storage_bucket" "profile_bucket" {
  name          = "${var.my_profile_name}-digital-twin-profile-bucket"
  location      = var.region
  force_destroy = true
}

resource "google_storage_bucket" "secondary_bucket" {
  name          = "${var.my_profile_name}-digital-twin-secondary-bucket"
  location      = var.region
  force_destroy = true
}


###############################################################
# 5. SECRET MANAGER — GITHUB TOKEN
# The what:
# This creates a secret in Secret Manager to store our GitHub token. This token is used by Cloud Build to authenticate with GitHub when pulling code for CI/CD.
# The why:
# Storing the GitHub token in Secret Manager keeps it secure and allows us to reference it in our Cloud Build configuration without hardcoding sensitive information in 
# any files that are easily accessible. This is a best practice for managing secrets and credentials in Google Cloud.
###############################################################


resource "google_secret_manager_secret" "github_token" {
  secret_id = "github-token"
  replication { automatic = true }
}

resource "google_secret_manager_secret_version" "github_token_version" {
  secret      = google_secret_manager_secret.github_token.id
  secret_data = var.github_token_value
}


###############################################################
# 6. CLOUD BUILD + GITHUB INTEGRATION
#
# This creates:
#   - GitHub connection
#   - Repo links
#   - Build triggers
#
# This is your CI/CD pipeline.
###############################################################

resource "google_cloudbuildv2_connection" "github_conn" {
  location = var.region
  name     = var.repo_connection_name

  github_config {
    app_installation_id = var.github_app_installation_id

    authorizer_credential {
      oauth_token_secret_version = google_secret_manager_secret_version.github_token_version.id
    }
  }
}

locals {
  github_repositories = {
    ui      = "https://github.com/${var.github_user}/${var.ui_repo_name}.git"
    service = "https://github.com/${var.github_user}/${var.service_repo_name}.git"
  }
}

resource "google_cloudbuildv2_repository" "my_repos" {
  for_each = local.github_repositories

  name              = "${var.repo_link_name}-${each.key}"
  parent_connection = google_cloudbuildv2_connection.github_conn.id
  remote_uri        = each.value
}

resource "google_cloudbuild_trigger" "github_triggers" {
  for_each = google_cloudbuildv2_repository.my_repos

  name     = "${var.trigger_name}-${each.key}"
  location = var.region

  repository_event_config {
    repository = each.value.id
    push { branch = "^main$" }
  }

  filename        = "cloudbuild.yaml"
  service_account = "projects/${data.google_project.project.project_id}/serviceAccounts/${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}


###############################################################
# 7. CLOUD RUN SERVICES — API + UI
#
# API = internal-only
# UI  = public (via load balancer)
###############################################################

resource "google_cloud_run_v2_service" "api_service" {
  name     = var.webservice_module_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_ONLY"

  template {
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }

    containers {
      image = "${var.region}-docker.pkg.dev/${data.google_project.project.project_id}/${var.repo_name}/${var.webservice_module_name}:latest"
    }
  }
}

resource "google_cloud_run_v2_service" "ui_service" {
  name     = var.website_module_name
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${data.google_project.project.project_id}/${var.repo_name}/digital-twin-ui:latest"

      env {
        name  = "SERVICE_URL"
        value = google_cloud_run_v2_service.api_service.uri
      }
    }
  }
}


###############################################################
# 8. LOAD BALANCER — PUBLIC ENTRYPOINT FOR UI
###############################################################

resource "google_compute_region_network_endpoint_group" "ui_neg" {
  name                  = "${var.my_org_name}-digital-twin-ui-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_v2_service.ui_service.name
  }
}

resource "google_compute_backend_service" "ui_backend" {
  name                  = "${var.my_org_name}-digital-twin-backend"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  protocol              = "HTTP"

  backend {
    group = google_compute_region_network_endpoint_group.ui_neg.id
  }
}

resource "google_compute_url_map" "ui_url_map" {
  name            = "${var.my_org_name}-digital-twin-url-map"
  default_service = google_compute_backend_service.ui_backend.id
}

resource "google_compute_global_address" "external_ip" {
  name = "${var.my_org_name}-https-ip"
}


###############################################################
# 9. CERTIFICATE MANAGER — MULTI-DOMAIN SSL
###############################################################

locals {
  domains = {
    root = "${var.root_domain}${var.tld}"
    www  = "${var.www_sub_domain}.${var.root_domain}${var.tld}"
    d1   = "${var.sub_domain1}.${var.root_domain}${var.tld}"
    d2   = "${var.sub_domain2}.${var.root_domain}${var.tld}"
  }
}

resource "google_certificate_manager_dns_authorization" "dns_auth" {
  for_each = local.domains

  name        = "auth-${var.root_domain}-${each.key}"
  domain      = each.value
  description = "DNS authorization for ${each.key} subdomain"
}

resource "google_certificate_manager_certificate" "managed_cert" {
  name        = "${var.root_domain}-managed-cert"
  description = "Managed certificate for all subdomains"

  managed {
    domains = [for d in local.domains : d]
    dns_authorizations = [
      for auth in google_certificate_manager_dns_authorization.dns_auth : auth.id
    ]
  }
}

resource "google_certificate_manager_certificate_map" "cert_map" {
  name        = "${var.root_domain}-cert-map"
  description = "Certificate map for digital twin"
}

resource "google_certificate_manager_certificate_map_entry" "cert_map_entry" {
  name         = "${var.root_domain}-cert-entry"
  map          = google_certificate_manager_certificate_map.cert_map.name
  certificates = [google_certificate_manager_certificate.managed_cert.id]
  hostname     = local.domains["root"]
}

resource "google_compute_target_https_proxy" "https_proxy" {
  name            = "${var.my_org_name}-https-proxy"
  url_map         = google_compute_url_map.ui_url_map.id
  certificate_map = google_certificate_manager_certificate_map.cert_map.id
}

resource "google_compute_global_forwarding_rule" "https_forwarding_rule" {
  name                  = "${var.my_org_name}-https-forwarding-rule"
  target                = google_compute_target_https_proxy.https_proxy.id
  port_range            = "443"
  load_balancing_scheme = "EXTERNAL_MANAGED"
  ip_address            = google_compute_global_address.external_ip.id
}


###############################################################
# 10. IAM — PERMISSIONS FOR CLOUD BUILD + COMPUTE
###############################################################

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
}

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
}