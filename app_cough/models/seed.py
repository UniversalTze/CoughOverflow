from .database import AsyncSession
from .dbmodels import Labs

async def seed_labs(file_path: str, db: AsyncSession): 
    with open(file_path, 'r', encoding="utf-8-sig", newline='') as csvfile:
        # Added encoding as csv had some buggy characters 
        for line in csvfile:
            # Process each line manually
            labid = line.strip()
            lab = Labs(id=labid)
            # Add lab entry to DB
            db.add(lab)
        #Commit changes to DB
        await db.commit()