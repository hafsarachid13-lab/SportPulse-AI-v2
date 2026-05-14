import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from backend.services.review_service import ReviewService

logger = logging.getLogger(__name__)

class NewsScheduler:
    """Orchestrateur pour les tâches planifiées de collecte de news."""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.review_service = ReviewService()
        self._setup_jobs()
        self._setup_listeners()

    def _setup_jobs(self):
        """Configure les jobs récurrents en utilisant le service de revue."""
        from datetime import datetime, timedelta
        
        # On utilise le service de revue pour bénéficier des verrous (locks)
        # On passe background=False ici car le scheduler fait déjà tourner la tâche en fond
        self.scheduler.add_job(
            func=self.review_service.generate_review,
            trigger=IntervalTrigger(minutes=60),
            id='hourly_scraping',
            name='Collecte automatique de news toutes les heures',
            replace_existing=True
        )
        logger.info("📅 Job de scraping horaire configuré via ReviewService")

    def _setup_listeners(self):
        """Configure les écouteurs d'événements pour le logging terminal."""
        def job_listener(event):
            if event.job_id == 'hourly_scraping':
                next_run = self.get_next_run_time()
                if next_run:
                    from datetime import datetime
                    next_dt = datetime.fromisoformat(next_run)
                    logger.info("=" * 60)
                    logger.info(f"✅ SYNCHRONISATION TERMINÉE")
                    logger.info(f"📅 PROCHAINE COLLECTE PRÉVUE LE : {next_dt.strftime('%d/%m/%Y à %H:%M:%S')}")
                    logger.info("=" * 60)

        self.scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

    def start(self):
        """Démarre le scheduler s'il n'est pas déjà lancé."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("🚀 Scheduler démarré avec succès")
            
            # Lancement immédiat au démarrage (en arrière-plan pour ne pas bloquer FastAPI)
            logger.info("⚡ Lancement de la collecte immédiate au démarrage...")
            self.review_service.generate_review(background=True)
            
            next_run = self.get_next_run_time()
            if next_run:
                from datetime import datetime
                next_dt = datetime.fromisoformat(next_run)
                logger.info(f"📅 PROCHAIN PASSAGE AUTOMATIQUE : {next_dt.strftime('%d/%m/%Y à %H:%M:%S')}")

    def shutdown(self):
        """Arrête proprement le scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Scheduler arrêté")

    def get_next_run_time(self):
        """Retourne la date du prochain passage du scheduler."""
        job = self.scheduler.get_job('hourly_scraping')
        if job and job.next_run_time:
            return job.next_run_time.isoformat()
        return None

# Instance globale
news_scheduler = NewsScheduler()

