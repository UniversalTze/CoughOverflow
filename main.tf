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
  image = docker_image.coughoverflow.name
  database_username = "cough_user" 
  database_password = "superSecretPassword.23"  # Bad to hardcode password in prod
} 

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
 vpc_id = data.aws_vpc.default.id # Good Software principles
 
 # Since no VPC created, it will used default VPC for region
 # Each AWS region has 6 subnets (one in each AZ). Internet gateway, rotue tables, etc included.
 # RDS instance will be assinged to all subnets
 ingress {  #Inbound (TCP port 5432) default for postgress
   from_port = 5432 
   to_port = 5432    # Default port for Postgress
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
   platform = "linux/amd64"
 } 
} 

resource "docker_registry_image" "coughoverflow_push" { 
 name = docker_image.coughoverflow.name
}

resource "aws_ecs_cluster" "coughoverflow" { 
   name = "coughoverflow" 
}

resource "aws_ecs_task_definition" "coughoverflow" {  #docker file exposes port 6400
   family = "coughoverflow"
   network_mode = "awsvpc" 
   requires_compatibilities = ["FARGATE"] 
   cpu = 1024 
   memory = 2048 
   execution_role_arn = data.aws_iam_role.lab.arn
   depends_on = [docker_registry_image.coughoverflow_push]
   runtime_platform {
    cpu_architecture        = "X86_64"
    operating_system_family = "LINUX"
  }

   container_definitions = <<DEFINITION
   [ 
   { 
    "image": "${local.image}",
    "cpu": 1024,
    "memory": 2048,
    "name": "coughoverflow", 
    "networkMode": "awsvpc", 
    "portMappings": [ 
      { 
       "containerPort": 6400,
       "hostPort": 6400 
      } 
    ],
     "environment": [ 
      { 
       "name": "SQLALCHEMY_DATABASE_URI", 
       "value": "postgresql://${local.database_username}:${local.database_password}@${aws_db_instance.coughoverflow_database.address}:${aws_db_instance.coughoverflow_database.port}/${aws_db_instance.coughoverflow_database.db_name}" 
      }
    ],
    "logConfiguration": { 
      "logDriver": "awslogs", 
      "options": { 
       "awslogs-group": "/coughoverflow/coughlogs", 
       "awslogs-region": "us-east-1", 
       "awslogs-stream-prefix": "ecs", 
       "awslogs-create-group": "true" 
      } 
    } 
   } 
 ]
   DEFINITION 
}

resource "aws_ecs_service" "coughoverflow" { 
   name = "coughoverflow" 
   cluster = aws_ecs_cluster.coughoverflow.id
   task_definition = aws_ecs_task_definition.coughoverflow.arn
   desired_count = 1 
   launch_type = "FARGATE" 
 
   network_configuration { 
    subnets = data.aws_subnets.private.ids
    security_groups = [aws_security_group.coughoverflow.id] 
    assign_public_ip = true 
   }
   
   depends_on = [ aws_db_instance.coughoverflow_database ]

   load_balancer { 
    target_group_arn = aws_lb_target_group.coughoverflow.arn
    container_name   = "coughoverflow" 
    container_port   = 6400 
  }
}

resource "aws_security_group" "coughoverflow" { 
   name = "coughoverflow" 
   description = "TaskOverflow Security Group" 
 
   ingress { 
    from_port = 6400 
    to_port = 6400 
    protocol = "tcp" 
    cidr_blocks = ["0.0.0.0/0"] 
   }
   
   egress { 
    from_port = 0 
    to_port = 0 
    protocol = "-1" 
    cidr_blocks = ["0.0.0.0/0"] 
   } 
}

################################### Load balancer
resource "aws_lb_target_group" "coughoverflow" {  # Used to send load to fargate instance
  name          = "coughoverflow" 
  port          = 6400 
  protocol      = "HTTP" 
  vpc_id        = aws_security_group.coughoverflow.vpc_id
  target_type   = "ip"
 
  health_check { 
    path                = "/api/v1/health" 
    port                = "6400" 
    protocol            = "HTTP" 
    healthy_threshold   = 2 
    unhealthy_threshold = 2 
    timeout             = 5 
    interval            = 60
  } 
}

resource "aws_lb" "coughoverflow" { 
  name               = "coughoverflow" 
  internal           = false 
  load_balancer_type = "application" 
  subnets            = data.aws_subnets.private.ids 
  security_groups    = [aws_security_group.coughoverflow_lb.id] 
} 

resource "aws_security_group" "coughoverflow_lb" { 
  name        = "coughoverflow_lb" 
  description = "CoughOverflow Load Balancer Security Group" 
 
  ingress { 
    from_port     = 80 
    to_port       = 80 
    protocol      = "tcp" 
    cidr_blocks   = ["0.0.0.0/0"] 
  } 
 
  egress { 
    from_port     = 0 
    to_port       = 0 
    protocol      = "-1" 
    cidr_blocks   = ["0.0.0.0/0"] 
  } 
 
  tags = { 
    Name = "coughoverflow_lb_security_group" 
  } 
}

resource "aws_lb_listener" "coughoverflow" { 
  load_balancer_arn   = aws_lb.coughoverflow.arn #ARN -> Amazon Resource Name
  port                = "80" 
  protocol            = "HTTP" 
 
  default_action { 
    type              = "forward" 
    target_group_arn  = aws_lb_target_group.coughoverflow.arn
  } 
}

############################ Auto Scaling
resource "aws_appautoscaling_target" "coughoverflow" { #uses string literals (api for different services)
  max_capacity        = 4 
  min_capacity        = 1 
  resource_id         = "service/coughoverflow/coughoverflow"  # resource_id = "service/<cluster_name>/<service_name>"
  scalable_dimension  = "ecs:service:DesiredCount" 
  service_namespace   = "ecs" 
 
  depends_on = [ aws_ecs_service.coughoverflow ] 
}

resource "local_file" "url" {
    content  = "http://${aws_lb.coughoverflow.dns_name}/api/v1"
    # "http://my-url/"  # Replace this string with a URL from your Terraform.
    filename = "./api.txt"
}
