resource "aws_sqs_queue" "worker_queue_normal" { 
   name = "cough-worker-normal-queue" 
   visibility_timeout_seconds = 240  # 4 minutes
}

resource "aws_sqs_queue" "worker_queue_urgent" { 
   name = "cough-worker-urgent.fifo" 
   fifo_queue = true
   content_based_deduplication =  true
   visibility_timeout_seconds = 240  # 4 minutes
}