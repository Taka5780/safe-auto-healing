resource "aws_cloudwatch_metric_alarm" "nginx_health_alarm" {
  alarm_name          = "safe-auto-healing-nginx-down"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "1"

  metric_name = "procstat_lookup_pid_count"
  namespace   = "CWAgent"
  period      = "60"
  statistic   = "Average"
  threshold   = "1"

  dimensions = {
    InstanceId = aws_instance.web.id
    exe        = "nginx"
    pid_finder = "native"
  }

  alarm_description = "This metric monitors nginx process and triggers auto-healing"
  alarm_actions     = [aws_lambda_function.recovery_lambda.arn]
  ok_actions        = [aws_lambda_function.recovery_lambda.arn]
}

resource "aws_cloudwatch_metric_alarm" "cpu_high_alarm" {
  alarm_name          = "human-decision-cpu-high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"

  metric_name = "CPUUtilization"
  namespace   = "AWS/EC2"
  period      = "60"
  statistic   = "Average"
  threshold   = "30"

  dimensions = {
    InstanceId = aws_instance.web.id
  }

  alarm_description = "This metric monitors ec2 cpu utilization and triggers investigation"

  alarm_actions = [aws_lambda_function.recovery_lambda.arn]
  ok_actions    = [aws_lambda_function.recovery_lambda.arn]
}
