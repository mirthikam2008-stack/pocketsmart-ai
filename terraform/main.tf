terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  type        = string
  description = "Google Cloud Project ID"
}

variable "region" {
  type        = string
  default     = "us-central1"
  description = "Default GCP deployment region"
}

# Secret Manager for Gemini API Key
resource "google_secret_manager_secret" "gemini_key" {
  secret_id = "GEMINI_API_KEY"
  replication {
    auto {}
  }
}

# Service Account for Cloud Run
resource "google_service_account" "pocketsmart_runner" {
  account_id   = "pocketsmart-cloudrun-sa"
  display_name = "PocketSmart AI Cloud Run Service Account"
}

resource "google_secret_manager_secret_iam_member" "secret_access" {
  secret_id = google_secret_manager_secret.gemini_key.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.pocketsmart_runner.email}"
}

# Google Cloud Run Service Deployment
resource "google_cloud_run_v2_service" "pocketsmart_service" {
  name     = "pocketsmart-ai"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.pocketsmart_runner.email

    scaling {
      min_instance_count = 1  # Retain warm instance to eliminate cold starts
      max_instance_count = 10
    }

    containers {
      image = "gcr.io/${var.project_id}/pocketsmart-ai:latest"
      resources {
        limits = {
          cpu    = "2000m"
          memory = "2Gi"
        }
        cpu_idle = false # Keep CPU always allocated for WebSocket stability
      }
      ports {
        container_port = 8080
      }
      env {
        name  = "PORT"
        value = "8080"
      }
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }
}

resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.pocketsmart_service.location
  name     = google_cloud_run_v2_service.pocketsmart_service.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "service_uri" {
  value       = google_cloud_run_v2_service.pocketsmart_service.uri
  description = "Production URL of deployed PocketSmart AI instance"
}
