resource "aws_sqs_queue" "worker_queue_normal" { 
   name = "cough-worker-normal" 
}

resource "aws_sqs_queue" "worker_queue_urgent" { 
   name = "cough-worker-urgent" 
}