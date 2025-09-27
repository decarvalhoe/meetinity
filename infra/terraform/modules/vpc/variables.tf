variable "name" {
  description = "Prefix for VPC related resource names."
  type        = string
}

variable "cidr_block" {
  description = "CIDR block assigned to the VPC."
  type        = string
}

variable "az_count" {
  description = "Number of availability zones to use."
  type        = number
  default     = 3
}

variable "public_subnet_cidrs" {
  description = "List of CIDRs for public subnets."
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "List of CIDRs for private subnets."
  type        = list(string)
}

variable "enable_nat_gateway" {
  description = "Whether to create a NAT gateway for private subnets."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags to apply to all resources."
  type        = map(string)
  default     = {}
}
