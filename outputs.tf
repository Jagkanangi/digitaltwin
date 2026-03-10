
output "dns_cname_records" {
  description = "The CNAME records you need to add to your DNS provider"
  value = {
    for k, v in google_certificate_manager_dns_authorization.dns_auth : 
    k => v.dns_resource_record
  }
}