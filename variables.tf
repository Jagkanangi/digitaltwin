###############################################################
# variables.tf — Teaching Version
#
# Every variable here is used by main.tf.
# Each one has a clear explanation for beginners.
###############################################################

variable "my_org_name" {
  description = "Short org identifier used in resource names (e.g. kindnus)"
  type        = string
}

variable "my_profile_name" {
  description = "Short profile/user identifier used in bucket names (e.g. jag)"
  type        = string
}

variable "organization_id" {
  description = "Your GCP organization ID"
  type        = string
}

variable "billing_account_id" {
  description = "Billing account ID for the project"
  type        = string
}

variable "region" {
  description = "Default region for all resources (e.g. us-central1)"
  type        = string
}

variable "root_domain" {
  description = "Root domain without TLD (e.g. example)"
  type        = string
}

variable "tld" {
  description = "Top-level domain (e.g. .com)"
  type        = string
}

variable "www_sub_domain" {
  description = "Subdomain for www (usually 'www')"
  type        = string
  default     = "www"
}

variable "sub_domain1" {
  description = "First additional subdomain (e.g. api)"
  type        = string
}

variable "sub_domain2" {
  description = "Second additional subdomain (e.g. ui)"
  type        = string
}

variable "github_app_installation_id" {
  description = "GitHub App installation ID used by Cloud Build"
  type        = number
}

variable "github_user" {
  description = "GitHub username or organization"
  type        = string
}

variable "ui_repo_name" {
  description = "GitHub repository name for the UI"
  type        = string
}

variable "service_repo_name" {
  description = "GitHub repository name for the API"
  type        = string
}

variable "repo_name" {
  description = "Artifact Registry repository ID for Docker images"
  type        = string
}

variable "repo_connection_name" {
  description = "Name for the Cloud Build GitHub connection"
  type        = string
}

variable "repo_link_name" {
  description = "Prefix for Cloud Build repository link resources"
  type        = string
}

variable "trigger_name" {
  description = "Prefix for Cloud Build triggers"
  type        = string
}

variable "webservice_module_name" {
  description = "Cloud Run service name for the API"
  type        = string
}

variable "website_module_name" {
  description = "Cloud Run service name for the UI"
  type        = string
}

variable "github_token_value" {
  description = "GitHub token stored in Secret Manager"
  type        = string
  sensitive   = true
}