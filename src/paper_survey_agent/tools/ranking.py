"""Paper ranking and deduplication tool."""

import logging
import re
from collections import Counter
from datetime import datetime
from typing import Optional

from rapidfuzz import fuzz

from paper_survey_agent.models.paper import Paper

logger = logging.getLogger(__name__)


def rank_and_deduplicate(
    papers: list[Paper],
    topic: str,
    top_k: int = 15,
    fuzzy_threshold: int = 85,
) -> list[Paper]:
    """Deduplicate and rank papers by relevance to topic.
    
    This function performs two main operations:
    1. Deduplication: Removes duplicate papers based on ID and fuzzy title matching
    2. Ranking: Scores papers by relevance, citations, and recency
    
    Args:
        papers: List of papers to rank and deduplicate
        topic: Research topic for relevance scoring
        top_k: Number of top papers to return (default: 15)
        fuzzy_threshold: Minimum similarity score (0-100) for duplicate detection (default: 85)
        
    Returns:
        Top-k ranked and deduplicated papers
    """
    logger.info(f"Ranking and deduplicating {len(papers)} papers for topic: '{topic}'")
    
    if not papers:
        logger.warning("No papers to rank")
        return []
    
    # Step 1: Deduplicate
    deduplicated = _deduplicate_papers(papers, fuzzy_threshold)
    logger.info(f"After deduplication: {len(deduplicated)} papers (removed {len(papers) - len(deduplicated)} duplicates)")
    
    # Step 2: Score each paper
    scored_papers = []
    for paper in deduplicated:
        score = _calculate_paper_score(paper, topic)
        scored_papers.append((paper, score))
    
    # Step 3: Sort by score (descending)
    scored_papers.sort(key=lambda x: x[1], reverse=True)
    
    # Step 4: Return top-k
    top_papers = [paper for paper, score in scored_papers[:top_k]]
    
    logger.info(
        f"Returning top {len(top_papers)} papers. "
        f"Score range: {scored_papers[0][1]:.3f} - {scored_papers[min(top_k-1, len(scored_papers)-1)][1]:.3f}"
    )
    
    return top_papers


def _deduplicate_papers(papers: list[Paper], fuzzy_threshold: int = 85) -> list[Paper]:
    """Remove duplicate papers based on ID and fuzzy title matching.
    
    Args:
        papers: List of papers to deduplicate
        fuzzy_threshold: Minimum similarity score (0-100) for duplicate detection
        
    Returns:
        Deduplicated list of papers
    """
    seen_ids = set()
    seen_titles = []
    deduplicated = []
    
    for paper in papers:
        # Check 1: Exact ID match
        if paper.id in seen_ids:
            logger.debug(f"Duplicate ID found: {paper.id} - {paper.title}")
            continue
        
        # Check 2: Fuzzy title matching
        is_duplicate = False
        normalized_title = _normalize_title(paper.title)
        
        for seen_title, seen_paper in seen_titles:
            similarity = fuzz.ratio(normalized_title, seen_title)
            if similarity >= fuzzy_threshold:
                logger.debug(
                    f"Fuzzy duplicate found ({similarity}% similar): "
                    f"'{paper.title}' ≈ '{seen_paper.title}'"
                )
                # Keep the one with more metadata (prefer one with citations)
                if paper.citations_count and not seen_paper.citations_count:
                    # Replace the seen paper with current one
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
    """Normalize title for comparison.
    
    Args:
        title: Paper title
        
    Returns:
        Normalized title (lowercase, no punctuation, single spaces)
    """
    # Convert to lowercase
    title = title.lower()
    # Remove special characters and punctuation
    title = re.sub(r'[^\w\s]', ' ', title)
    # Replace multiple spaces with single space
    title = re.sub(r'\s+', ' ', title)
    # Strip whitespace
    title = title.strip()
    return title


def _calculate_paper_score(paper: Paper, topic: str) -> float:
    """Calculate relevance score for a paper.
    
    Score is a weighted combination of:
    - Relevance to topic (TF-IDF-like keyword matching)
    - Citation count (normalized)
    - Recency (newer papers score higher)
    - PDF availability (small bonus)
    
    Args:
        paper: Paper to score
        topic: Research topic
        
    Returns:
        Combined score (0.0 - 1.0+)
    """
    # Component 1: Relevance (0.0 - 1.0)
    relevance = _calculate_relevance(paper, topic)
    
    # Component 2: Citation score (0.0 - 1.0)
    citation_score = _calculate_citation_score(paper)
    
    # Component 3: Recency score (0.0 - 1.0)
    recency_score = _calculate_recency_score(paper)
    
    # Component 4: PDF availability bonus
    pdf_bonus = 0.1 if paper.pdf_url else 0.0
    
    # Weighted combination
    # Higher weight on relevance, moderate on citations, lower on recency
    score = (
        0.4 * relevance +
        0.3 * citation_score +
        0.2 * recency_score +
        0.1 * pdf_bonus
    )
    
    logger.debug(
        f"Paper: {paper.title[:50]}... | "
        f"Relevance: {relevance:.2f} | Citations: {citation_score:.2f} | "
        f"Recency: {recency_score:.2f} | PDF: {pdf_bonus:.1f} | Total: {score:.3f}"
    )
    
    return score


def _calculate_relevance(paper: Paper, topic: str) -> float:
    """Calculate relevance of paper to topic using keyword matching.
    
    Uses TF-IDF-inspired approach:
    - Extracts keywords from topic
    - Counts occurrences in title and abstract
    - Normalizes by text length
    
    Args:
        paper: Paper to score
        topic: Research topic
        
    Returns:
        Relevance score (0.0 - 1.0)
    """
    # Extract keywords from topic (lowercase, remove stopwords)
    topic_keywords = _extract_keywords(topic)
    
    if not topic_keywords:
        return 0.5  # Neutral score if no keywords
    
    # Combine title and abstract for searching
    text = f"{paper.title} {paper.abstract}".lower()
    
    # Count keyword occurrences
    keyword_counts = Counter()
    for keyword in topic_keywords:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(keyword) + r'\b'
        count = len(re.findall(pattern, text))
        if count > 0:
            keyword_counts[keyword] = count
    
    # Calculate score
    if not keyword_counts:
        return 0.1  # Low score if no keywords found
    
    # Score based on:
    # - Number of unique keywords found
    # - Frequency of keywords
    # - Bonus for keywords in title
    unique_keywords_found = len(keyword_counts)
    total_occurrences = sum(keyword_counts.values())
    
    # Keywords in title get 2x weight
    title_lower = paper.title.lower()
    title_matches = sum(1 for kw in topic_keywords if kw in title_lower)
    
    # Normalize scores
    keyword_coverage = unique_keywords_found / len(topic_keywords)
    frequency_score = min(total_occurrences / (len(topic_keywords) * 3), 1.0)
    title_boost = min(title_matches / len(topic_keywords) * 0.5, 0.5)
    
    score = min(keyword_coverage * 0.5 + frequency_score * 0.3 + title_boost, 1.0)
    
    return score


def _extract_keywords(text: str) -> list[str]:
    """Extract meaningful keywords from text.
    
    Args:
        text: Input text
        
    Returns:
        List of keywords (lowercase, no stopwords)
    """
    # Common stopwords in English
    stopwords = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'this', 'these', 'those', 'using',
        'based', 'can', 'we', 'our', 'use', 'used', 'how', 'what', 'when',
    }
    
    # Normalize and split
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    words = text.split()
    
    # Filter stopwords and short words
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    
    return keywords


def _calculate_citation_score(paper: Paper) -> float:
    """Calculate normalized citation score.
    
    Uses log scale to prevent extremely high citation counts from dominating.
    
    Args:
        paper: Paper to score
        
    Returns:
        Citation score (0.0 - 1.0)
    """
    if paper.citations_count is None or paper.citations_count <= 0:
        return 0.0
    
    # Log scale normalization
    # Typical highly-cited papers: 100-1000 citations
    # Exceptional papers: 1000+ citations
    import math
    score = math.log10(paper.citations_count + 1) / math.log10(1001)
    
    return min(score, 1.0)


def _calculate_recency_score(paper: Paper) -> float:
    """Calculate recency score based on publication date.
    
    Recent papers (last 2 years) score highest.
    Papers older than 10 years score lowest.
    
    Args:
        paper: Paper to score
        
    Returns:
        Recency score (0.0 - 1.0)
    """
    current_year = datetime.now().year
    paper_year = paper.published_date.year
    age_years = current_year - paper_year
    
    if age_years < 0:
        # Future date (possible error), treat as very recent
        return 1.0
    elif age_years <= 2:
        # Very recent (0-2 years)
        return 1.0
    elif age_years <= 5:
        # Recent (3-5 years)
        return 0.8
    elif age_years <= 10:
        # Moderately old (6-10 years)
        return 0.5
    else:
        # Old (10+ years)
        # Still give some credit, especially for classic papers
        return max(0.2, 1.0 - (age_years - 10) / 20)
