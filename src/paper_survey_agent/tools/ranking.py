from collections import Counter
from datetime import datetime
import logging
import re
from typing import Optional

from rapidfuzz import fuzz

from paper_survey_agent.models.paper import Paper
from paper_survey_agent.settings import settings


logger = logging.getLogger(__name__)


def rank_and_deduplicate(
    papers: list[Paper],
    topic: str,
    top_k: int = settings.MAX_PAPERS_TO_RETURN,
    fuzzy_threshold: int = settings.RANKING_FUZZY_THRESHOLD,
) -> list[Paper]:
    logger.info(f"Ranking and deduplicating {len(papers)} papers for topic: '{topic}'")

    if not papers:
        logger.warning("No papers to rank")
        return []

    deduplicated = _deduplicate_papers(papers, fuzzy_threshold)
    logger.info(
        f"After deduplication: {len(deduplicated)} papers (removed {len(papers) - len(deduplicated)} duplicates)"
    )

    scored_papers = []
    for paper in deduplicated:
        score = _calculate_paper_score(paper, topic)
        scored_papers.append((paper, score))

    scored_papers.sort(key=lambda x: x[1], reverse=True)

    top_papers = [paper for paper, score in scored_papers[:top_k]]

    if scored_papers:
        logger.info(
            f"Returning top {len(top_papers)} papers. "
            f"Score range: {scored_papers[0][1]:.3f} - {scored_papers[min(top_k-1, len(scored_papers)-1)][1]:.3f}"
        )

    return top_papers


def _deduplicate_papers(papers: list[Paper], fuzzy_threshold: int) -> list[Paper]:
    seen_ids = set()
    seen_titles = []
    deduplicated = []

    for paper in papers:
        if paper.id in seen_ids:
            logger.debug(f"Duplicate ID found: {paper.id} - {paper.title}")
            continue

        is_duplicate = False
        normalized_title = _normalize_title(paper.title)

        for seen_title, seen_paper in seen_titles:
            similarity = fuzz.ratio(normalized_title, seen_title)
            if similarity >= fuzzy_threshold:
                logger.debug(
                    f"Fuzzy duplicate found ({similarity}% similar): " f"'{paper.title}' ≈ '{seen_paper.title}'"
                )
                if paper.citations_count and not seen_paper.citations_count:
                    deduplicated.remove(seen_paper)
                    seen_ids.remove(seen_paper.id)
                    seen_titles.remove((seen_title, seen_paper))
                else:
                    is_duplicate = True
                    break

        if not is_duplicate:
            seen_ids.add(paper.id)
            seen_titles.append((normalized_title, paper))
            deduplicated.append(paper)

    return deduplicated


def _normalize_title(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^\w\s]", " ", title)
    title = re.sub(r"\s+", " ", title)
    title = title.strip()
    return title


def _calculate_paper_score(paper: Paper, topic: str) -> float:
    relevance = _calculate_relevance(paper, topic)
    citation_score = _calculate_citation_score(paper)
    recency_score = _calculate_recency_score(paper)
    pdf_bonus = settings.WEIGHT_PDF_BONUS if paper.pdf_url else 0.0

    score = (
        settings.WEIGHT_RELEVANCE * relevance
        + settings.WEIGHT_CITATIONS * citation_score
        + settings.WEIGHT_RECENCY * recency_score
        + pdf_bonus
    )

    logger.debug(
        f"Paper: {paper.title[:50]}... | "
        f"Relevance: {relevance:.2f} | Citations: {citation_score:.2f} | "
        f"Recency: {recency_score:.2f} | PDF Bonus: {pdf_bonus:.1f} | Total: {score:.3f}"
    )

    return score


def _calculate_relevance(paper: Paper, topic: str) -> float:
    topic_keywords = _extract_keywords(topic)
    if not topic_keywords:
        return 0.5

    text = f"{paper.title} {paper.abstract}".lower()
    keyword_counts = Counter()
    for keyword in topic_keywords:
        pattern = r"\b" + re.escape(keyword) + r"\b"
        count = len(re.findall(pattern, text))
        if count > 0:
            keyword_counts[keyword] = count

    if not keyword_counts:
        return 0.1

    unique_keywords_found = len(keyword_counts)
    total_occurrences = sum(keyword_counts.values())
    title_lower = paper.title.lower()
    title_matches = sum(1 for kw in topic_keywords if kw in title_lower)

    keyword_coverage = unique_keywords_found / len(topic_keywords)
    frequency_score = min(total_occurrences / (len(topic_keywords) * 3), 1.0)
    title_boost = min(title_matches / len(topic_keywords) * 0.5, 0.5)

    score = min(keyword_coverage * 0.5 + frequency_score * 0.3 + title_boost, 1.0)
    return score


def _extract_keywords(text: str) -> list[str]:
    stopwords = {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "he",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "that",
        "the",
        "to",
        "was",
        "will",
        "with",
        "this",
        "these",
        "those",
        "using",
        "based",
        "can",
        "we",
        "our",
        "use",
        "used",
        "how",
        "what",
        "when",
    }
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    words = text.split()
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    return keywords


def _calculate_citation_score(paper: Paper) -> float:
    if paper.citations_count is None or paper.citations_count <= 0:
        return 0.0
    import math

    score = math.log10(paper.citations_count + 1) / math.log10(1001)
    return min(score, 1.0)


def _calculate_recency_score(paper: Paper) -> float:
    current_year = datetime.now().year
    paper_year = paper.published_date.year
    age_years = current_year - paper_year

    if age_years < 0:
        return 1.0
    elif age_years <= settings.RECENCY_VERY_RECENT:
        return 1.0
    elif age_years <= settings.RECENCY_RECENT:
        return 0.8
    elif age_years <= settings.RECENCY_MODERATE:
        return 0.5
    else:
        return max(0.2, 1.0 - (age_years - settings.RECENCY_MODERATE) / 20)
