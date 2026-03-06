terraform {
  required_version = ">= 1.5"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
    # DNS providers — only the one matching var.dns_provider is actively used.
    # All must be declared here so `terraform init` downloads them.
    # Credentials are only validated at plan/apply time for modules that run.
    hetznerdns = {
      source  = "timohirt/hetznerdns"
      version = "~> 2.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }

  # Local state is used by default. To use a remote backend, uncomment and
  # configure one of the blocks below.
  #
  # --- Option A: Terraform Cloud / HCP Terraform ---
  # cloud {
  #   organization = "your-org"
  #   workspaces {
  #     name = "porthole-hub"
  #   }
  # }
  #
  # --- Option B: S3-compatible remote backend (e.g. AWS S3, DigitalOcean Spaces) ---
  # backend "s3" {
  #   bucket                      = "your-tf-state-bucket"
  #   key                         = "porthole/hub/terraform.tfstate"
  #   region                      = "us-east-1"
  #   # For DigitalOcean Spaces, also set:
  #   # endpoint                  = "https://nyc3.digitaloceanspaces.com"
  #   # skip_credentials_validation = true
  #   # skip_metadata_api_check    = true
  #   # skip_region_validation     = true
  #   # force_path_style           = true
  # }
}
