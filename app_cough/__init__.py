# app/__init__.py 
# Handling imports
from app_cough.views.healthroute import healthrouter
from app_cough.views.labroute import labrouter
from app_cough.views.analysisroute import analysisrouter
from app_cough.views.resultsroute import resultRouter
from app_cough import utils
from app_cough.tasks.analysis import send_startup_message