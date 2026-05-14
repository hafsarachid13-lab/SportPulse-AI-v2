import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

from backend.services.export_service import ExportService

data = {
    "title": "Test Review",
    "date": "2026-05-12T01:07:38",
    "metadata": {
        "total_articles": 10,
        "sources_count": 2,
        "categories_count": 3,
        "avg_importance": 0.8,
        "avg_credibility": 0.9
    },
    "sections": {
        "executive_summary": {
            "text": "Ceci est un test en français. وهذا اختبار باللغة العربية."
        }
    },
    "categories": {
        "Football": [
            {"title": "Test Article", "source": "Source A", "summary": "Summary here", "importance_score": 0.9}
        ]
    }
}

try:
    service = ExportService()
    filename = service.generate_pdf(data, "test_premium.pdf")
    print(f"Success! Generated {filename}")
except Exception as e:
    import traceback
    traceback.print_exc()
