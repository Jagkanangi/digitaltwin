# variables.tf

variable "root_domain" {
  type        = string
  description = "The name of your domain (e.g., kindnus)"
}

variable "organization_id" {
  type        = string
}

variable "region" {
  type    = string
  default = "northamerica-northeast2" # You can keep defaults for non-private stuff
}

variable "tld" {
  type        = string
  description = "Top-level domain"
}

variable "www_sub_domain" {
  type        = string
  description = "WWW subdomain"

}

variable "sub_domain1" {
  type        = string
  description = "Subdomain 1"
}

variable "sub_domain2" {
  type        = string
  description = "Subdomain 2"
}

variable "github_user" {
  type        = string
  description = "GitHub username"
}

variable "gcp_git_installation_id" {
  type        = string
  description = "GCP Git installation ID"
}

variable "chroma_password" {
  type        = string
  description = "ChromaDB password"
  sensitive   = true
}

variable "redis_password" {
  type        = string
  description = "Redis password"
  sensitive   = true
}

variable "open_ai_key" {
  type        = string
  description = "OpenAI API Key"
  sensitive   = true
}

variable "chroma_db" {
  type        = string
  description = "ChromaDB service URL"
}

variable "redis_service" {
  type        = string
  description = "Redis service URL"
}

variable "ip_address" {
  type        = string
  description = "External IP address"
}

variable "website_module_name" {
  type        = string
  description = "The name for the digital twin UI website module"
  default     = "digital-twin-ui-website"
}

variable "webservice_module_name" {
  type        = string
  description = "The name for the digital twin API service module"
  default     = "digital-twin-api-service"
}

variable "backend_service_name" {
  type        = string
  description = "The name of the backend service"
}

variable "NEG_name" {
  type        = string
  description = "The name of the Network Endpoint Group (NEG)"
}

variable "url_map" {
  type        = string
  description = "The name of the URL map"
}

variable "ssl_certificates" {
  type        = string
  description = "The name of the SSL certificates"
}

variable "cert_map" {
  type        = string
  description = "The name of the certificate map"
}


variable "https_proxy" {
  type        = string
  description = "The name of the HTTPS proxy"
  default     = "https-proxy"
}

variable "repo_name" {
  type        = string
  description = "The name of the repository"
  default = "digital-twin-repo"
}

variable "github_repo" {
  type        = string
  description = "The name of the GitHub repository"
}

variable "trigger_name" {
  type        = string
  description = "The name of the trigger"
  default = "digital-twin-trigger"
}

variable "repo_connection_name" {
  type        = string
  description = "The name of the repository connection"
  default = "digital-twin-github-connection"
}

variable "repo_link_name" {
  type        = string
  description = "The name of the repository link"
  default = "repo-link"
}

variable "chroma_bucket_name" {
  type        = string
  description = "The name of the Chroma bucket"
}

variable "redis_bucket_name" {
  type        = string
  description = "The name of the Redis bucket"
}

variable "secret_keys" {
  type        = list(string)
  description = "A list of secret keys to be created in Secret Manager"
  default     = ["CHROMA_SERVER_AUTH_CREDENTIALS", "REDIS_PASSWORD", "OPENAI_API_KEY"]
}

variable "ui_repo_name" {
  type        = string
  description = "The name of the GitHub repository for the UI"
  default = "MyProfileWebsite"
}

variable "service_repo_name" {
  type        = string
  description = "The name of the GitHub repository for the UI"
  default = "digitaltwin"
}