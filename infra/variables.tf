variable "region" {
  type    = string
  default = "us-east-1"
}

variable "aws_profile" {
  type    = string
  default = "fiap-gs"
}

variable "instance_type" {
  type    = string
  default = "t3.large"
}

variable "ssh_public_key_path" {
  type    = string
  default = "~/.ssh/civiclens-cicd.pub"
}

variable "admin_cidrs" {
  type        = list(string)
  description = "IPs autorizados a acessar SSH, Jenkins, SonarQube e app"
}

variable "github_hook_cidrs" {
  type        = list(string)
  description = "Faixas IPv4 de origem dos webhooks do GitHub (gh api meta --jq .hooks)"
}
