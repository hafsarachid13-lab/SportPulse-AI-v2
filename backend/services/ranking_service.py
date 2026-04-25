
from ai_agent.ranking import score_importance

def get_article_score(article_text: str):
    score = score_importance(article_text)

    return {
        "success": True,
        "score": score
    }

    #hafsa