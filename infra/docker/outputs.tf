output "container_name" {
  description = "Name of the managed Docker container."
  value       = docker_container.dataset_preflight.name
}

output "health_url" {
  description = "Local readiness endpoint for the managed service."
  value       = "http://127.0.0.1:${var.port}/health/ready"
}
