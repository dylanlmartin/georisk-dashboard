import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from ..database import get_db
from ..services.gdelt_service import GDELTService
from ..services.worldbank_service import WorldBankService
from ..services.event_processing_service import EventProcessingService
from ..services.feature_engineering_service import FeatureEngineeringService
from ..services.ml_risk_scoring_service import MLRiskScoringService
from ..core.logging import get_logger

logger = get_logger(__name__)

class SchedulerService:
    """
    Automated scheduler for data collection and ML pipeline execution
    Implements collection schedule from technical specification
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis_client = redis_client
        self.gdelt_service = GDELTService(redis_client)
        self.worldbank_service = WorldBankService(redis_client)
        self.event_processing_service = EventProcessingService()
        self.feature_engineering_service = FeatureEngineeringService()
        self.ml_service = MLRiskScoringService()
        
        # Schedule configuration from technical spec
        self.schedules = {
            "gdelt_events": {"interval_hours": 6, "last_run_key": "last_gdelt_run"},
            "worldbank_indicators": {"interval_hours": 168, "last_run_key": "last_wb_run"},  # Weekly
            "event_processing": {"interval_hours": 1, "last_run_key": "last_processing_run"},
            "feature_engineering": {"interval_hours": 24, "last_run_key": "last_features_run"},
            "risk_scoring": {"interval_hours": 24, "last_run_key": "last_scoring_run"},
            "model_retraining": {"interval_hours": 168, "last_run_key": "last_training_run"}  # Weekly
        }
    
    async def run_scheduler(self):
        """
        Main scheduler loop - checks and runs tasks based on schedule
        """
        logger.info("Starting automated scheduler")
        
        while True:
            try:
                current_time = datetime.now()
                
                # Check each scheduled task
                for task_name, config in self.schedules.items():
                    try:
                        should_run = await self._should_run_task(
                            task_name, 
                            config["interval_hours"], 
                            config["last_run_key"]
                        )
                        
                        if should_run:
                            logger.info(f"Running scheduled task: {task_name}")
                            await self._run_task(task_name)
                            await self._update_last_run(config["last_run_key"], current_time)
                            
                    except Exception as e:
                        logger.error(f"Error in scheduled task {task_name}: {str(e)}")
                        continue
                
                # Sleep for 1 hour before next check
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"Error in scheduler main loop: {str(e)}")
                await asyncio.sleep(300)  # Short sleep on error
    
    async def _should_run_task(self, task_name: str, interval_hours: int, last_run_key: str) -> bool:
        """Check if a task should run based on its schedule"""
        try:
            last_run_str = await self.redis_client.get(last_run_key)
            
            if not last_run_str:
                # Never run before
                return True
            
            last_run = datetime.fromisoformat(last_run_str.decode())
            time_since_run = datetime.now() - last_run
            
            return time_since_run.total_seconds() >= (interval_hours * 3600)
            
        except Exception as e:
            logger.error(f"Error checking schedule for {task_name}: {str(e)}")
            return False
    
    async def _update_last_run(self, last_run_key: str, run_time: datetime):
        """Update the last run timestamp for a task"""
        try:
            await self.redis_client.set(
                last_run_key, 
                run_time.isoformat(),
                ex=86400 * 7  # Expire after 1 week
            )
        except Exception as e:
            logger.error(f"Error updating last run time: {str(e)}")
    
    async def _run_task(self, task_name: str):
        """Execute a specific scheduled task"""
        async with get_db() as session:
            try:
                if task_name == "gdelt_events":
                    await self._run_gdelt_collection(session)
                    
                elif task_name == "worldbank_indicators":
                    await self._run_worldbank_collection(session)
                    
                elif task_name == "event_processing":
                    await self._run_event_processing(session)
                    
                elif task_name == "feature_engineering":
                    await self._run_feature_engineering(session)
                    
                elif task_name == "risk_scoring":
                    await self._run_risk_scoring(session)
                    
                elif task_name == "model_retraining":
                    await self._run_model_retraining(session)
                    
                else:
                    logger.warning(f"Unknown task: {task_name}")
                    
            except Exception as e:
                logger.error(f"Error executing task {task_name}: {str(e)}")
                raise
    
    async def _run_gdelt_collection(self, session: AsyncSession):
        """Collect events from GDELT API"""
        logger.info("Starting GDELT event collection")
        
        try:
            all_events = await self.gdelt_service.collect_all_countries_events(session)
            
            total_events = sum(len(events) for events in all_events.values())
            successful_countries = sum(1 for events in all_events.values() if events)
            
            logger.info(f"GDELT collection completed: {total_events} events from {successful_countries} countries")
            
        except Exception as e:
            logger.error(f"GDELT collection failed: {str(e)}")
            raise
    
    async def _run_worldbank_collection(self, session: AsyncSession):
        """Collect indicators from World Bank API"""
        logger.info("Starting World Bank indicator collection")
        
        try:
            all_data = await self.worldbank_service.collect_all_countries_indicators(session)
            
            successful_countries = sum(1 for data in all_data.values() if data)
            total_indicators = sum(len(data) for data in all_data.values())
            
            logger.info(f"World Bank collection completed: {total_indicators} indicator sets from {successful_countries} countries")
            
        except Exception as e:
            logger.error(f"World Bank collection failed: {str(e)}")
            raise
    
    async def _run_event_processing(self, session: AsyncSession):
        """Process raw events through NLP pipeline"""
        logger.info("Starting event processing")
        
        try:
            processed_count = await self.event_processing_service.process_raw_events(
                session, batch_size=1000
            )
            
            logger.info(f"Event processing completed: {processed_count} events processed")
            
        except Exception as e:
            logger.error(f"Event processing failed: {str(e)}")
            raise
    
    async def _run_feature_engineering(self, session: AsyncSession):
        """Generate features for ML pipeline"""
        logger.info("Starting feature engineering")
        
        try:
            target_date = datetime.now().date()
            success_count = await self.feature_engineering_service.generate_and_store_features_for_all_countries(
                session, target_date
            )
            
            logger.info(f"Feature engineering completed: {success_count} countries processed")
            
        except Exception as e:
            logger.error(f"Feature engineering failed: {str(e)}")
            raise
    
    async def _run_risk_scoring(self, session: AsyncSession):
        """Generate risk scores using ML models"""
        logger.info("Starting ML risk scoring")
        
        try:
            # Load models if not already loaded
            if not self.ml_service.models_trained():
                model_loaded = await self.ml_service.load_models()
                if not model_loaded:
                    logger.warning("No trained models available for scoring")
                    return
            
            # Get all countries
            from sqlalchemy import select
            from ..models import Country
            
            result = await session.execute(select(Country.id, Country.name))
            countries = result.fetchall()
            
            target_date = datetime.now().date()
            success_count = 0
            
            for country_id, country_name in countries:
                try:
                    predictions = await self.ml_service.predict_risk_scores(
                        session, country_id, target_date
                    )
                    
                    if predictions:
                        stored = await self.ml_service.store_predictions(session, predictions)
                        if stored:
                            success_count += 1
                            
                except Exception as e:
                    logger.warning(f"Failed to score {country_name}: {str(e)}")
                    continue
            
            logger.info(f"Risk scoring completed: {success_count}/{len(countries)} countries scored")
            
        except Exception as e:
            logger.error(f"Risk scoring failed: {str(e)}")
            raise
    
    async def _run_model_retraining(self, session: AsyncSession):
        """Retrain ML models with latest data"""
        logger.info("Starting model retraining")
        
        try:
            training_results = await self.ml_service.train_models(session)
            
            if "error" in training_results:
                logger.error(f"Model training failed: {training_results['error']}")
            else:
                logger.info(f"Model retraining completed: {training_results['training_samples']} samples")
                
        except Exception as e:
            logger.error(f"Model retraining failed: {str(e)}")
            raise
    
    async def run_manual_task(self, task_name: str) -> Dict[str, Any]:
        """Manually trigger a specific task"""
        logger.info(f"Manually running task: {task_name}")
        
        try:
            async with get_db() as session:
                await self._run_task(task_name)
                
                # Update last run time
                if task_name in self.schedules:
                    await self._update_last_run(
                        self.schedules[task_name]["last_run_key"],
                        datetime.now()
                    )
                
                return {
                    "status": "success",
                    "task": task_name,
                    "completed_at": datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Manual task {task_name} failed: {str(e)}")
            return {
                "status": "error",
                "task": task_name,
                "error": str(e),
                "failed_at": datetime.now().isoformat()
            }
    
    async def get_schedule_status(self) -> Dict[str, Any]:
        """Get status of all scheduled tasks"""
        status = {}
        
        for task_name, config in self.schedules.items():
            try:
                last_run_str = await self.redis_client.get(config["last_run_key"])
                
                if last_run_str:
                    last_run = datetime.fromisoformat(last_run_str.decode())
                    next_run = last_run + timedelta(hours=config["interval_hours"])
                    
                    status[task_name] = {
                        "interval_hours": config["interval_hours"],
                        "last_run": last_run.isoformat(),
                        "next_run": next_run.isoformat(),
                        "overdue": datetime.now() > next_run
                    }
                else:
                    status[task_name] = {
                        "interval_hours": config["interval_hours"],
                        "last_run": None,
                        "next_run": "pending",
                        "overdue": True
                    }
                    
            except Exception as e:
                logger.error(f"Error getting status for {task_name}: {str(e)}")
                status[task_name] = {"error": str(e)}
        
        return status