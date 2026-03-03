terraform {
  required_version = ">= 1.5"

  required_providers {
    hcloud = {
      source  = "hetznercloud/hcloud"
      version = "~> 1.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.0"
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
