variable "key_name" {
  description = "Name of the SSH key pair"
  type        = string
}

variable "instance_type" {
  default = "t3.micro"
}

variable "slack_webhook_url" {
  description = "Slack Incoming Webhook URL"
  type        = string
  sensitive   = true
}
