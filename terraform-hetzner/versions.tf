terraform {
  required_version = ">= 1.5"

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.0"
    }
    # hetznerdns manages the Hetzner DNS public API (dns.hetzner.com).
    # The correct registry source is timohirt/hetznerdns (v2.x).
    # "hetzner-community/hetznerdns" does NOT exist in registry.terraform.io.
    # "germanbrew/hetznerdns" is deprecated (Nov 2025); the official hcloud
    # provider's new DNS resources target a different (beta) DNS system.
    # Run this directory with the HashiCorp terraform binary, not tofu.
    hetznerdns = {
      source  = "timohirt/hetznerdns"
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
