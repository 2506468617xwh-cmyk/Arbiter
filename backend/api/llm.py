from fastapi import APIRouter

from backend.schemas.llm import LLMChatRequest, LLMQuickSummaryRequest, LLMResponse, PetSummaryRequest
from backend.services.llm_service import answer_research_question, generate_pet_summary, generate_quick_summary


router = APIRouter(tags=["llm"])


@router.post("/llm/quick-summary", response_model=LLMResponse)
def create_quick_summary(request: LLMQuickSummaryRequest) -> LLMResponse:
    return generate_quick_summary(request)


@router.post("/llm/chat", response_model=LLMResponse)
def create_chat_answer(request: LLMChatRequest) -> LLMResponse:
    return answer_research_question(request)


@router.post("/llm/pet-summary", response_model=LLMResponse)
def create_pet_summary(request: PetSummaryRequest) -> LLMResponse:
    return generate_pet_summary(request)
