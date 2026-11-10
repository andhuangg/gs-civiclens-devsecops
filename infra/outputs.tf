output "public_ip" {
  value = aws_eip.cicd.public_ip
}

output "jenkins_url" {
  value = "http://${aws_eip.cicd.public_ip}:8080/"
}

output "sonarqube_url" {
  value = "http://${aws_eip.cicd.public_ip}:9000/"
}

output "app_url" {
  value = "http://${aws_eip.cicd.public_ip}:8000/"
}

output "github_webhook_url" {
  value = "http://${aws_eip.cicd.public_ip}:8080/github-webhook/"
}

output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "ssh" {
  value = "ssh -i ~/.ssh/civiclens-cicd ubuntu@${aws_eip.cicd.public_ip}"
}
