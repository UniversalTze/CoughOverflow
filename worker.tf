resource "docker_image" "coughoverflow-engine" { 
 name = "${aws_ecr_repository.coughoverflow-engine.repository_url}:latest" 
 build { 
   context = "." #build image locally
   dockerfile = "Dockerfile-Engine"
   platform = "linux/amd64"
 } 
} 

resource "aws_ecr_repository" "coughoverflow-engine" { #ECR Registry for engine
 name = "coughoverflow-engine"
}

resource "docker_registry_image" "coughoverflow-engine_push" { 
 name = docker_image.coughoverflow-engine.name
}

resource "aws_ecs_task_definition" "coughoverflow-engine" {  #docker file exposes port 6400
   family = "coughoverflow-engine"
   network_mode = "awsvpc" 
   requires_compatibilities = ["FARGATE"] 
   cpu = 4096
   memory = 8192
   execution_role_arn = data.aws_iam_role.lab.arn
   task_role_arn = data.aws_iam_role.lab.arn
   depends_on = [docker_registry_image.coughoverflow_push]
   runtime_platform {
    cpu_architecture        = "X86_64"
    operating_system_family = "LINUX"
  }

   container_definitions = <<DEFINITION
   [ 
   { 
    "image": "${local.engine_image}",
    "cpu": 4096,
    "memory": 8192,
    "name": "coughoverflow-engine",
    "environment": [
      {
      "name": "CELERY_BROKER_URL",
      "value": "sqs://"
      },
      {
      "name": "CELERY_RESULT_BACKEND",
      "value": "db+postgresql://${local.database_username}:${local.database_password}@${aws_db_instance.coughoverflow_database.address}:${aws_db_instance.coughoverflow_database.port}/${aws_db_instance.coughoverflow_database.db_name}"
      },
      { 
       "name": "SQLALCHEMY_DATABASE_URI", 
       "value": "postgresql+asyncpg://${local.database_username}:${local.database_password}@${aws_db_instance.coughoverflow_database.address}:${aws_db_instance.coughoverflow_database.port}/${aws_db_instance.coughoverflow_database.db_name}" 
      },
      {
      "name": "SQLALCHEMY_SYNC_DATABASE_URI",
      "value": "postgresql://${local.database_username}:${local.database_password}@${aws_db_instance.coughoverflow_database.address}:${aws_db_instance.coughoverflow_database.port}/${aws_db_instance.coughoverflow_database.db_name}"
      },
      { "name": "NORMAL_QUEUE", "value": "cough-worker-normal.fifo"},
      { "name": "NORMAL_QUEUE_MIN", "value": "2"},
      { "name": "NORMAL_QUEUE_MAX", "value": "10"},
      { "name": "URGENT_QUEUE", "value": "cough-worker-urgent.fifo"},
      { "name": "URGENT_QUEUE_MIN", "value": "2"},
      { "name": "URGENT_QUEUE_MAX", "value": "20"}
    ],
    "logConfiguration": { 
      "logDriver": "awslogs", 
      "options": { 
       "awslogs-group": "/coughoverflowengine/coughlogs", 
       "awslogs-region": "us-east-1", 
       "awslogs-stream-prefix": "ecs", 
       "awslogs-create-group": "true" 
      } 
    } 
   } 
 ]
   DEFINITION 
}

############################ Auto Scaling
resource "aws_appautoscaling_target" "coughoverflow-engine" { #uses string literals (api for different services)
  max_capacity        = 12
  min_capacity        = 1 
  resource_id         = "service/coughoverflow/coughoverflow-engine"  # resource_id = "service/<cluster_name>/<service_name>"
  scalable_dimension  = "ecs:service:DesiredCount" 
  service_namespace   = "ecs" 
 
  depends_on = [ aws_ecs_service.coughoverflow ] 
}

###### Scaling based on CPU usage
resource "aws_appautoscaling_policy" "coughoverflow-engine-cpu" { 
  name                = "coughoverflow-cpu" 
  policy_type         = "TargetTrackingScaling" 
  resource_id         = aws_appautoscaling_target.coughoverflow-engine.id 
  scalable_dimension  = aws_appautoscaling_target.coughoverflow-engine.scalable_dimension 
  service_namespace   = aws_appautoscaling_target.coughoverflow-engine.service_namespace
 
  target_tracking_scaling_policy_configuration { 
    predefined_metric_specification { 
      predefined_metric_type  = "ECSServiceAverageCPUUtilization" 
    } 
    target_value              = 40    # CPU value %
    scale_in_cooldown         = 60
    scale_out_cooldown        = 30 
  } 
}

resource "aws_ecs_service" "coughoverflow-engine" { 
   name = "coughoverflow-engine" 
   cluster = aws_ecs_cluster.coughoverflow.id
   task_definition = aws_ecs_task_definition.coughoverflow-engine.arn
   desired_count = 1 
   launch_type = "FARGATE" 
 
   network_configuration { 
    subnets = data.aws_subnets.private.ids
    assign_public_ip = true
    security_groups = [aws_security_group.coughoverflow_engine.id]
   }

     depends_on = [ aws_ecs_cluster.coughoverflow ] 
}

resource "aws_security_group" "coughoverflow_engine" { 
  name        = "coughoverflow_engine" 
  description = "CoughOverflow engine Security Group" 
 
  egress { 
    from_port     = 0 
    to_port       = 0 
    protocol      = "-1" 
    cidr_blocks   = ["0.0.0.0/0"] 
  } 
 
  tags = { 
    Name = "coughoverflow_engine_security_group" 
  } 
}

################## Scaling Out
resource "aws_cloudwatch_metric_alarm" "nornalqueue_scale_out" {
  alarm_name          = "ecs-normalqueue-scale-out-on-queue-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 30
  statistic           = "Average"
  threshold           = 30
  alarm_description   = "Scale out when visible messages > 40"
  dimensions = {
    QueueName = aws_sqs_queue.worker_queue_normal.name
  }

  alarm_actions = [aws_appautoscaling_policy.queue-overflow-step-scaling.arn]
}

resource "aws_cloudwatch_metric_alarm" "urgentqueue_scale_out" {
  alarm_name          = "ecs-urgentqueue-scale-out-on-queue-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 30
  statistic           = "Average"
  threshold           = 30
  alarm_description   = "Scale out when visible messages > 40"
  dimensions = {
    QueueName = aws_sqs_queue.worker_queue_urgent.name
  }

  alarm_actions = [aws_appautoscaling_policy.queue-overflow-step-scaling.arn]
}

resource "aws_cloudwatch_metric_alarm" "normal_queue_scale_in" {
  alarm_name          = "scale-in-normal-queue"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 30
  statistic           = "Average"
  threshold           = 15
  alarm_description   = "Scale in if normal queue has < 15 visible messages"
  dimensions = {
    QueueName = aws_sqs_queue.worker_queue_normal.name
  }
  alarm_actions = [aws_appautoscaling_policy.queue-overflow-step-scaling.arn]
}

resource "aws_cloudwatch_metric_alarm" "urgent_queue_scale_in" {
  alarm_name          = "scale-in-urgent-queue"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 30
  statistic           = "Average"
  threshold           = 15
  alarm_description   = "Scale in if urgent queue has < 15 visible messages"
  dimensions = {
    QueueName = aws_sqs_queue.worker_queue_urgent.name
  }
  alarm_actions = [aws_appautoscaling_policy.queue-overflow-step-scaling.arn]
}

resource "aws_appautoscaling_policy" "queue-overflow-step-scaling" { 
  name                = "queue-over-flow-scale-out" 
  policy_type         = "StepScaling" 
  resource_id         = aws_appautoscaling_target.coughoverflow-engine.id 
  scalable_dimension  = aws_appautoscaling_target.coughoverflow-engine.scalable_dimension 
  service_namespace   = aws_appautoscaling_target.coughoverflow-engine.service_namespace

  step_scaling_policy_configuration {
    adjustment_type         = "ChangeInCapacity"
    cooldown                = 60
    metric_aggregation_type = "Average"

    step_adjustment {
      scaling_adjustment = 1
      metric_interval_lower_bound = 30
    }
    # No-op for 15 <= x < 40
    step_adjustment {
      scaling_adjustment = 0
      metric_interval_lower_bound = 15
      metric_interval_upper_bound = 30
}
    step_adjustment {
      scaling_adjustment = -1
      metric_interval_upper_bound = 15
    }
  }
}