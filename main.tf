terraform {
    required_providers {
        aws = {
            source  = "hashicorp/aws"
            version = "~> 4.0"
        }
        docker = { 
            source = "kreuzwerker/docker" 
            version = "3.0.2" 
    } 
    }
}

provider "aws" {
    region = "us-east-1"
    shared_credentials_files = ["./credentials"]
    default_tags {
        tags = { # For metadata, # Key value pairs. (all resources created will inherit these tags, unless overrided).
            Course       = "CSSE6400"
            Name         = "CoughOverflow"
            Automation   = "Terraform"
            Owner        = "UniversalTze"
            StudentID    = "s4703754"
        }
    }
}

data "aws_vpc" "default" {  # default VPC for given AWS region
   default = true 
} 

data "aws_subnets" "private" {  # All Subnets within the default VPC
   filter { 
      name = "vpc-id" 
      values = [data.aws_vpc.default.id] 
   } 
}

data "aws_iam_role" "lab" { 
  # From AWS, this role is like a super user, can do everything within AWS console.
  name = "LabRole"
}

# Resource
locals {
    database_username = "cough_user" 
    database_password = "superSecretPassword.23"  # Bad to hardcode password in prod
} 

/*
resource "aws_db_instance" "coughoverflow_database" { 
 allocated_storage = 20   # MIN GB
 max_allocated_storage = 1000  # MAX GB (scale up)
 engine = "postgres" 
 engine_version = "17" 
 instance_class = "db.t3.micro"    # small, low-cost instance
 db_name = "cough" 
 username = local.database_username 
 password = local.database_password 
 parameter_group_name = "default.postgres17"  # defalult group settings for this DB
 skip_final_snapshot = true     # Skip creating a backup snapshot when deleted
 vpc_security_group_ids = [aws_security_group.coughoverflow_database.id]    # security group for network access
 publicly_accessible = true  # Access over the internet
 allow_major_version_upgrade = true   # upgrading version of engien. 
 
 tags = { 
   Name = "coughoverflow_database" 
 } 
}

resource "aws_security_group" "coughoverflow_database" { 
 name = "coughoverflow_database"  # Name of security group in AWS
 description = "Set up inbound and outbound Postgresql traffic" 
 
 # Since no VPC created, it will used default VPC for region
 # Each AWS region has 6 subnets (one in each AZ). Internet gateway, rotue tables, etc included.
 # RDS instance will be assinged to all subnets
 ingress {  #Inbound (TCP port 5432) default for postgress
   from_port = 5432 
   to_port = 5432 
   protocol = "tcp" 
   cidr_blocks = ["0.0.0.0/0"] #Any IPv4 address
 } 
 
 egress { #outbound (all outbound traffic)
   from_port = 0 
   to_port = 0 
   protocol = "-1" #represents all
   cidr_blocks = ["0.0.0.0/0"]  #IPv4
   ipv6_cidr_blocks = ["::/0"]  #IPv6
 } 
 
 tags = { 
   Name = "coughoverflow_database"   #metadata (AWS generic tagging system)
   # Commonly used for display in AWS consoles
 } 
}

output "db_endpoint" {
  description = "The address to connect to the PostgreSQL database"
  value       = aws_db_instance.coughoverflow_database.endpoint
}

output "db_port" {
  description = "Database port"
  value       = aws_db_instance.coughoverflow_database.port
}
*/
# For docker authorisation
data "aws_ecr_authorization_token" "ecr_token" {} 
 
provider "docker" { 
 registry_auth { 
   address = data.aws_ecr_authorization_token.ecr_token.proxy_endpoint 
   username = data.aws_ecr_authorization_token.ecr_token.user_name 
   password = data.aws_ecr_authorization_token.ecr_token.password 
 } 
}

resource "aws_ecr_repository" "coughoverflow" { #ECR Registry
 name = "coughoverflow"
}


resource "docker_image" "coughoverflow" { 
 name = "${aws_ecr_repository.coughoverflow.repository_url}:latest" 
 build { 
   context = "." #build image locally
 } 
} 

resource "docker_registry_image" "coughoverflow_push" { 
 name = docker_image.coughoverflow.name
}

/*
resource "local_file" "url" {
    content  = "http://my-url/"  # Replace this string with a URL from your Terraform.
    filename = "./api.txt"
}
*/