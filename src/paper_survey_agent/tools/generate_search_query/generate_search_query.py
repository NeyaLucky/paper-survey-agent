from loguru import logger

from paper_survey_agent.llm.client import llm_client
from paper_survey_agent.llm.prompts import SEARCH_QUERY_REFINEMENT_SYSTEM_PROMPT


def generate_search_query(user_query: str) -> str:
    logger.info(f"🧠 Refining user query: '{user_query}'")

    user_prompt = f"User Input: {user_query}\n\nRefined Search Query:"

    try:
        refined_query = llm_client.generate(prompt=user_prompt, system_prompt=SEARCH_QUERY_REFINEMENT_SYSTEM_PROMPT)

        refined_query = refined_query.strip().strip('"').strip("'")

        logger.info(f"✨ Refined query: '{refined_query}'")
        return refined_query

    except Exception as e:
        logger.error(f"Failed to refine query, falling back to original: {e}")
        return user_query
