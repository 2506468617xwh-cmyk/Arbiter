"""API endpoint for AI Market Intelligence (Narrative Engine)."""
from fastapi import APIRouter

from backend.schemas.news_intelligence import NewsIntelligenceResponse
from backend.services.news_intelligence_service import get_news_intelligence

router = APIRouter(tags=["news-intelligence"])


@router.get("/news/intelligence", response_model=NewsIntelligenceResponse)
def read_news_intelligence(use_llm: bool = True) -> NewsIntelligenceResponse:
    return get_news_intelligence(use_llm=use_llm)
