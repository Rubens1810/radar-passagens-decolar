output "dynamodb_table_name" {
  value = aws_dynamodb_table.price_history.name
}

output "lambda_function_name" {
  value = aws_lambda_function.radar_worker.function_name
}

output "schedule_rule_name" {
  value = aws_cloudwatch_event_rule.daily_scan.name
}