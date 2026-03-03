output "hub_ip" {
  description = "Public IPv4 address of the hub server."
  value       = hcloud_server.hub.ipv4_address
}

output "server_id" {
  description = "Hetzner Cloud server ID of the hub node."
  value       = hcloud_server.hub.id
}
