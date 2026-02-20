"""
=================================================================
  NLP Pipeline — Text preprocessing and analysis for EV data.
  
  Used for:
    - Cleaning station names and categories (normalization)
    - Sentiment analysis on user reviews (if available)
    - Topic modeling to find common charger issues
=================================================================
"""

import re
import pandas as pd
import numpy as np
from typing import List, Optional


# ──────────────────────────────────────────────────────
#  TEXT CLEANING (Basic — no external dependencies)
# ──────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Basic text cleaning for any string field.
    
    Steps:
      1. Lowercase
      2. Remove special characters (keep alphanumeric + spaces)
      3. Remove extra whitespace
      4. Strip
    """
    if pd.isna(text) or not isinstance(text, str):
        return ""
    
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_text_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Apply text cleaning to an entire column."""
    df = df.copy()
    if column in df.columns:
        df[f"{column}_clean"] = df[column].apply(clean_text)
        print(f"  🔤 Cleaned text column: {column} → {column}_clean")
    return df


# ──────────────────────────────────────────────────────
#  TOKENIZATION & STOPWORDS (No external deps)
# ──────────────────────────────────────────────────────

# Common English stopwords + EV domain-specific noise words
STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
    "as", "into", "through", "during", "before", "after", "above", "below",
    "between", "out", "off", "over", "under", "again", "further", "then",
    "once", "here", "there", "when", "where", "why", "how", "all", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "not",
    "only", "own", "same", "so", "than", "too", "very", "and", "but",
    "or", "nor", "if", "this", "that", "it", "its", "i", "me", "my",
    "we", "our", "you", "your", "he", "him", "his", "she", "her",
    "they", "them", "their", "what", "which", "who", "whom",
    # EV noise words
    "station", "charging", "ev", "electric", "vehicle", "charger",
}


def tokenize(text: str) -> List[str]:
    """Split text into tokens, removing stopwords."""
    if not text:
        return []
    words = text.split()
    return [w for w in words if w not in STOPWORDS and len(w) > 2]


def get_word_frequencies(texts: List[str], top_n: int = 20) -> pd.DataFrame:
    """
    Get the most common words across all texts.
    Useful for understanding what users talk about.
    """
    from collections import Counter
    
    all_words = []
    for text in texts:
        all_words.extend(tokenize(clean_text(text)))
    
    freq = Counter(all_words).most_common(top_n)
    return pd.DataFrame(freq, columns=["word", "count"])


# ──────────────────────────────────────────────────────
#  SENTIMENT ANALYSIS (Rule-based — no ML needed)
# ──────────────────────────────────────────────────────

# EV-domain sentiment lexicon
POSITIVE_WORDS = {
    "good", "great", "excellent", "fast", "quick", "reliable", "clean",
    "convenient", "easy", "working", "available", "friendly", "nice",
    "smooth", "efficient", "perfect", "awesome", "best", "love", "happy",
    "satisfied", "recommend", "maintained", "functional", "operational",
}

NEGATIVE_WORDS = {
    "bad", "slow", "broken", "dirty", "expensive", "unavailable", "closed",
    "fault", "error", "issue", "problem", "complaint", "poor", "worst",
    "terrible", "awful", "stuck", "malfunction", "damaged", "occupied",
    "blocked", "crowded", "waiting", "delayed", "failed", "crash",
    "overpriced", "unreliable", "dangerous", "unsafe", "scam",
}


def simple_sentiment(text: str) -> dict:
    """
    Rule-based sentiment scoring.
    
    Returns:
        {"score": float (-1 to 1), "label": "positive"/"negative"/"neutral"}
    """
    tokens = tokenize(clean_text(text))
    
    if not tokens:
        return {"score": 0.0, "label": "neutral", "positive_count": 0, "negative_count": 0}
    
    pos = sum(1 for t in tokens if t in POSITIVE_WORDS)
    neg = sum(1 for t in tokens if t in NEGATIVE_WORDS)
    total = pos + neg
    
    if total == 0:
        score = 0.0
    else:
        score = (pos - neg) / total
    
    label = "positive" if score > 0.1 else ("negative" if score < -0.1 else "neutral")
    
    return {
        "score": round(score, 3),
        "label": label,
        "positive_count": pos,
        "negative_count": neg,
    }


def analyze_sentiment_column(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    """
    Apply sentiment analysis to a text column.
    
    Adds columns: sentiment_score, sentiment_label
    """
    df = df.copy()
    
    if text_col not in df.columns:
        print(f"  ⚠️  Column '{text_col}' not found")
        return df
    
    sentiments = df[text_col].fillna("").apply(simple_sentiment)
    sentiment_df = pd.DataFrame(sentiments.tolist())
    
    df["sentiment_score"] = sentiment_df["score"]
    df["sentiment_label"] = sentiment_df["label"]
    
    pos_pct = (df["sentiment_label"] == "positive").mean() * 100
    neg_pct = (df["sentiment_label"] == "negative").mean() * 100
    
    print(f"  💬 Sentiment analysis on '{text_col}':")
    print(f"     Positive: {pos_pct:.1f}% | Negative: {neg_pct:.1f}% | Neutral: {100-pos_pct-neg_pct:.1f}%")
    
    return df


# ──────────────────────────────────────────────────────
#  TOPIC EXTRACTION (Keyword-based grouping)
# ──────────────────────────────────────────────────────

TOPIC_KEYWORDS = {
    "payment_issues": ["payment", "pay", "card", "upi", "money", "refund", "bill", "charge"],
    "hardware_fault": ["broken", "damaged", "screen", "cable", "connector", "plug", "hardware"],
    "app_issues": ["app", "software", "login", "otp", "crash", "error", "update"],
    "availability": ["available", "occupied", "blocked", "queue", "waiting", "busy"],
    "speed_quality": ["slow", "fast", "speed", "power", "kilowatt", "kw", "rate"],
    "location_access": ["location", "parking", "access", "find", "direction", "map"],
    "cleanliness": ["clean", "dirty", "maintained", "hygiene", "trash", "toilet"],
}


def extract_topics(text: str) -> List[str]:
    """Identify which topics a text belongs to."""
    tokens = set(tokenize(clean_text(text)))
    topics = []
    
    for topic, keywords in TOPIC_KEYWORDS.items():
        if tokens.intersection(keywords):
            topics.append(topic)
    
    return topics if topics else ["general"]


def analyze_topics(df: pd.DataFrame, text_col: str) -> pd.DataFrame:
    """
    Extract topics from a text column.
    
    Adds column: topics (list of topic labels)
    """
    df = df.copy()
    
    if text_col not in df.columns:
        print(f"  ⚠️  Column '{text_col}' not found")
        return df
    
    df["topics"] = df[text_col].fillna("").apply(extract_topics)
    
    # Count topic frequencies
    from collections import Counter
    all_topics = []
    for topics in df["topics"]:
        all_topics.extend(topics)
    
    freq = Counter(all_topics)
    print(f"  📊 Topic distribution:")
    for topic, count in freq.most_common():
        print(f"     {topic}: {count} mentions")
    
    return df
