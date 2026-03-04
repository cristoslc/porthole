# ---------------------------------------------------------------------------
# backend.tf — Remote state backend configuration
#
# WHY THIS MATTERS:
#   Without remote state, Terraform only works from the machine where
#   "terraform apply" was first run. If that machine is unavailable when
#   the hub needs to be rebuilt (disaster recovery), Terraform has no record
#   of existing resources — risking orphaned DNS records, duplicate servers,
#   or lost firewall rules. Remote state makes any workstation viable.
#   (Addresses SPEC-008, JOURNEY-004.PP-01)
#
# SETUP (choose one):
#
# --- Option A: Terraform Cloud / HCP Terraform (recommended — free tier) ---
#   1. Create a free account at https://app.terraform.io
#   2. Create an organization and a workspace named "porthole-hub"
#      (or update the name below)
#   3. Run: terraform login
#   4. Uncomment the block below and fill in your organization name.
#   5. Run: terraform init   (migrates any existing local state)
#
# cloud {
#   organization = "your-org-name"
#   workspaces {
#     name = "porthole-hub"
#   }
# }
#
# --- Option B: S3-compatible backend (AWS S3, DigitalOcean Spaces, etc.) ---
#   1. Create a bucket for Terraform state.
#   2. Uncomment and configure the block below.
#   3. Run: terraform init -reconfigure
#
# backend "s3" {
#   bucket = "your-tf-state-bucket"
#   key    = "porthole/hub/terraform.tfstate"
#   region = "us-east-1"
#
#   # For DigitalOcean Spaces, also set:
#   # endpoint                     = "https://nyc3.digitaloceanspaces.com"
#   # skip_credentials_validation  = true
#   # skip_metadata_api_check      = true
#   # skip_region_validation       = true
#   # force_path_style             = true
# }
#
# --- Option C: Local state (default — single workstation only) ---
#   No configuration needed. Terraform stores state in terraform.tfstate
#   locally. Back this file up manually if using this option. DO NOT commit
#   terraform.tfstate to version control.
# ---------------------------------------------------------------------------
