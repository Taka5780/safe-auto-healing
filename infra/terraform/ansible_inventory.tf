resource "local_file" "ansible_inventory" {
  content = <<EOT
[web]
${aws_instance.web.public_ip} ansible_user=ec2-user ansible_ssh_private_key_file=~/.ssh/${var.key_name}.pem
EOT

  filename = "../ansible/inventory"
}
