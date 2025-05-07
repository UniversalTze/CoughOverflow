resource "aws_sqs_queue" "worker_queue_normal" { 
   name = "cough-worker-normal.fifo" 
   fifo_queue = true
   content_based_deduplication =  true
}

resource "aws_sqs_queue" "worker_queue_urgent" { 
   name = "cough-worker-urgent.fifo" 
   fifo_queue = true
   content_based_deduplication =  true
}