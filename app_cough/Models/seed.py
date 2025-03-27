from .database import SessionLocal
from .dbmodels import Labs

def seed_labs(file_path: str): 
    db = SessionLocal()
    with open(file_path, newline='') as csvfile:
        try:
            for line in csvfile:
            # Process each line manually
                labid = line.strip()
                lab = Labs(id=labid)
                # Add lab entry
                db.add(lab)
            #Commit changes to DB
            db.commit()
        finally: 
            db.close()