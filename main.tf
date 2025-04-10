terraform {
    required_providers {
        aws = {
            source  = "hashicorp/aws"
            version = "~> 4.0"
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
/*
# Resource
locals {
    image = "ghcr.io/csse6400/taskoverflow:latest"  # Currently incorrect, need to change this with image in registry
    database_username = "administrator" 
    database_password = "foobarbaz" # This is bad! 
} 

resource "aws_ecr_repository" "coughOverflow" { #ECR Registry
 name = "coughoverflow" 
}

resource "aws_security_group" "coughOverflow_database" { 
 name = "coughoverflow_database"  # Name of security group in AWS
 description = "Set up inbound and outbound Postgresql traffic" 
 
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

resource "docker_image" "coughOverflow" { 
 name = "${aws_ecr_repository.coughoverflow}:latest" 
 build { 
   context = "." #build image locally
 } 
} 


resource "local_file" "url" {
    content  = "http://my-url/"  # Replace this string with a URL from your Terraform.
    filename = "./api.txt"
}
*/