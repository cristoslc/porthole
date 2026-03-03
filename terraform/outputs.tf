output "hub_ip" {
  description = "Public IPv4 address of the hub Droplet."
  value       = digitalocean_droplet.hub.ipv4_address
}

output "droplet_id" {
  description = "DigitalOcean Droplet ID of the hub node."
  value       = digitalocean_droplet.hub.id
}
