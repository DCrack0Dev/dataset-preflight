terraform {
  required_version = ">= 1.6.0"
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_image" "dataset_preflight" {
  name = var.image_name
  build {
    context    = abspath("${path.module}/../..")
    dockerfile = "Dockerfile"
  }
  keep_locally = true
}

resource "docker_container" "dataset_preflight" {
  name  = var.container_name
  image = docker_image.dataset_preflight.image_id

  must_run = true
  restart  = "unless-stopped"

  ports {
    internal = 8080
    external = var.port
  }

  read_only = true
  tmpfs     = { "/tmp" = "" }
  user      = "65534:65534"

  security_opts = ["no-new-privileges:true"]

  healthcheck {
    test         = ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health/ready')"]
    interval     = "10s"
    timeout      = "3s"
    retries      = 3
    start_period = "5s"
  }
}
