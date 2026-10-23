variable "image_name" {
  description = "Local image tag built from the repository Dockerfile."
  type        = string
  default     = "dataset-preflight:terraform"
}

variable "container_name" {
  description = "Name assigned to the running validation service container."
  type        = string
  default     = "dataset-preflight"
}

variable "port" {
  description = "Host port forwarded to the service's internal port 8080."
  type        = number
  default     = 8080

  validation {
    condition     = var.port >= 1024 && var.port <= 65535
    error_message = "port must be an unprivileged TCP port between 1024 and 65535."
  }
}
