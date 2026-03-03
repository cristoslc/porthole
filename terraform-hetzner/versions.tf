terraform {
  required_version = ">= 1.5"

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.0"
    }
    # DNS providers — only the one matching var.dns_provider is actively used.
    # All three must be declared here so `terraform init` downloads them.
    # Credentials are only validated at plan/apply time for modules that run.
    #
    # hetznerdns: timohirt/hetznerdns (v2.x) targets dns.hetzner.com API.
    # "hetzner-community/hetznerdns" does NOT exist in registry.terraform.io.
    # Run this directory with the HashiCorp terraform binary, not tofu —
    # hetznerdns is only in the Terraform registry, not the OpenTofu registry.
    hetznerdns = {
      source  = "timohirt/hetznerdns"
      version = "~> 2.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }

  # Local state is used by default. To use a remote backend, uncomment one of:
  #
  # --- Option A: Terraform Cloud / HCP Terraform ---
  # cloud {
  #   organization = "your-org"
  #   workspaces {
  #     name = "porthole-hub-hetzner"
  #   }
  # }
  #
  # --- Option B: S3-compatible remote backend ---
  # backend "s3" {
  #   bucket = "your-tf-state-bucket"
  #   key    = "porthole/hub-hetzner/terraform.tfstate"
  #   region = "us-east-1"
  # }
}
