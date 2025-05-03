resource "aws_sqs_queue" "worker_queue" { 
   name = "cough-worker" 
}