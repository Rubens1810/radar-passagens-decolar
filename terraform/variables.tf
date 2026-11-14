variable "aws_region" {
  description = "Região AWS para deploy"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefixo dos recursos do projeto"
  type        = string
  default     = "flight-price-radar"
}

variable "serpapi_key" {
  description = "Chave da API da SerpApi"
  type        = string
  sensitive   = true
}

variable "discord_webhook_url" {
  description = "URL do Webhook do Discord"
  type        = string
  sensitive   = true
}