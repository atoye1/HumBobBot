from fastapi import APIRouter, Depends, BackgroundTasks # Added BackgroundTasks
from sqlalchemy.orm import Session
from starlette import status

from database import  get_db, SessionLocal # Added SessionLocal
from models import Regulation
from domain.regulation import regulation_crud, regulation_schema
from RegulationCrawler import RegulationCrawler # Assuming RegulationCrawler.py is in the root
import logging # For logging within the endpoint

router = APIRouter(
    prefix="/regulation",
)

# Create a logger for this router
logger = logging.getLogger(__name__)

def run_crawler_tasks():
    db_session_for_crawler = None
    try:
        logger.info("Crawler task started by /regulation/update endpoint.")
        db_session_for_crawler = SessionLocal() # Create a new session for the background task
        crawler = RegulationCrawler(db_session=db_session_for_crawler)
        logger.info("Calling crawler.crawl()...")
        crawler.crawl()
        logger.info("Calling crawler.handle_file_process()...")
        crawler.handle_file_process()
        logger.info("Crawler tasks completed.")
    except Exception as e:
        logger.error(f"Error during crawler tasks: {e}", exc_info=True)
    finally:
        if db_session_for_crawler:
            db_session_for_crawler.close()
        logger.info("Crawler task resources released.")

@router.post('/skill')
def regulation_skill(_regulation_skill: regulation_schema.RegulationSkill,
                     db:Session = Depends(get_db)):
    _regulation_list = db.query(Regulation).order_by(Regulation.create_date.desc()).all()
    return _regulation_list

@router.post('/update', status_code=status.HTTP_202_ACCEPTED) # Use 202 for accepted background task
async def regulation_update(background_tasks: BackgroundTasks): # Removed db: Session = Depends(get_db) as the task creates its own session
    logger.info("Received request to /regulation/update. Adding crawler tasks to background.")
    background_tasks.add_task(run_crawler_tasks)
    return {"message": "Regulation update process started in the background."}