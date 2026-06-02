"""
Transformer-based abstractive summarizer for EchoText MoM generation.

Uses Qwen/Qwen2.5-0.5B-Instruct for structured Minutes of Meeting (MoM) and MoM Summary.
Falls back to TF-IDF extractive summarization structured templates if the model is unavailable.
"""

import re
import math
import os
from collections import Counter
from typing import Optional
from datetime import datetime

# ---------------------------------------------------------------------------
# Transformer model (lazy-loaded on first use)
# ---------------------------------------------------------------------------

_pipeline = None
_pipeline_tried = False

def _get_pipeline():
    """Lazy-load the summarization pipeline. Returns None if unavailable."""
    global _pipeline, _pipeline_tried
    if _pipeline_tried:
        return _pipeline
    _pipeline_tried = True
    try:
        from transformers import pipeline as hf_pipeline
        print("[Summarizer] Loading Qwen/Qwen2.5-0.5B-Instruct model...")
        _pipeline = hf_pipeline(
            "text-generation",
            model="Qwen/Qwen2.5-0.5B-Instruct",
            device=-1,          # CPU
        )
        print("[Summarizer] Model loaded successfully.")
    except Exception as e:
        print(f"[Summarizer] Could not load Qwen model: {e}. Using TF-IDF fallback.")
        _pipeline = None
    return _pipeline


# ---------------------------------------------------------------------------
# TF-IDF extractive fallback
# ---------------------------------------------------------------------------

STOPWORDS = {
    "a","an","the","and","or","but","in","on","at","to","for","of","with",
    "is","are","was","were","be","been","being","have","has","had","do","does",
    "did","will","would","could","should","may","might","shall","can","need",
    "i","we","you","he","she","they","it","this","that","these","those",
    "my","your","his","her","our","their","its","me","him","us","them",
    "so","if","as","by","from","about","into","through","during","then",
    "just","not","also","very","well","like","there","here","up","out",
    "what","which","who","when","where","how","then","than","more","all",
    "some","any","one","two","three","no","yes","ok","okay","uh","um","yeah"
}


def _tokenize(text: str) -> list[str]:
    return re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())


def _split_sentences(text: str) -> list[str]:
    sents = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sents if len(s.strip().split()) >= 4]


def _tfidf_scores(sentences: list[str]) -> list[float]:
    if not sentences:
        return []
    all_words = _tokenize(" ".join(sentences))
    doc_freq = Counter(w for w in all_words if w not in STOPWORDS)
    total_docs = len(sentences)
    scores = []
    for sent in sentences:
        words = [w for w in _tokenize(sent) if w not in STOPWORDS]
        if not words:
            scores.append(0.0)
            continue
        tf = Counter(words)
        score = sum(
            (tf[w] / len(words)) * math.log(1 + total_docs / (doc_freq.get(w, 1)))
            for w in tf
        )
        scores.append(score)
    return scores


def _extractive_summary(text: str, num_sentences: int = 5) -> str:
    sentences = _split_sentences(text)
    if not sentences:
        return text[:500]
    scores = _tfidf_scores(sentences)
    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
    top_indices = sorted([i for i, _ in ranked[:num_sentences]])
    return " ".join(sentences[i] for i in top_indices)


# ---------------------------------------------------------------------------
# Key topic extraction
# ---------------------------------------------------------------------------

def _extract_topics(text: str, n: int = 6) -> list[str]:
    words = [w for w in _tokenize(text) if w not in STOPWORDS]
    freq = Counter(words)
    return [w.capitalize() for w, _ in freq.most_common(n * 2) if len(w) > 3][:n]


# ---------------------------------------------------------------------------
# Action item & decision detection
# ---------------------------------------------------------------------------

ACTION_PATTERNS = [
    r"\b(need to|needs to|should|will|must|have to|going to|plan to)\b.{5,80}",
    r"\b(action item|task|todo|to-do|follow up|follow-up)\b.{0,80}",
    r"\b(assign(ed)? to|responsible for)\b.{3,80}",
    r"\b(please|kindly)\s+\w+.{3,60}",
    r"\b(by (monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|next week|eod|eow))\b.{0,60}",
]

DECISION_PATTERNS = [
    r"\b(decided|agreed|confirmed|concluded|resolved|approved|rejected)\b.{3,80}",
    r"\b(we will go with|going with|final decision|we chose|we selected)\b.{3,80}",
    r"\b(consensus|unanimous|agreement)\b.{3,80}",
]


def _extract_actions_and_decisions(text: str):
    sentences = _split_sentences(text)
    action_items, decisions = [], []
    seen_actions, seen_decisions = set(), set()

    for sent in sentences:
        sent_clean = sent.strip()
        sent_lower = sent_clean.lower()

        for pat in ACTION_PATTERNS:
            if re.search(pat, sent_lower):
                key = sent_lower[:40]
                if key not in seen_actions:
                    seen_actions.add(key)
                    action_items.append(sent_clean)
                break

        for pat in DECISION_PATTERNS:
            if re.search(pat, sent_lower):
                key = sent_lower[:40]
                if key not in seen_decisions:
                    seen_decisions.add(key)
                    decisions.append(sent_clean)
                break

    return action_items[:8], decisions[:6]


def _extractive_fallback_mom(text: str, word_count: int, duration_min: int) -> dict:
    """Generate structured MoM layouts using extractive fallback heuristic."""
    topics = _extract_topics(text, n=6)
    action_items, decisions = _extract_actions_and_decisions(text)
    
    # Format Fallback MoM markdown
    mom_lines = [
        "# MINUTES OF MEETING (MoM)",
        "",
        "## Meeting Details",
        "- **Project/Team Name:** (Local Fallback)",
        "- **Meeting Title:** Transcription Summary",
        f"- **Date:** {datetime.now().strftime('%d/%m/%Y')}",
        "- **Time:** Unknown",
        "- **Venue/Platform:** Local System",
        "- **Meeting Conducted By:** Unknown",
        "- **Minutes Prepared By:** EchoText (Fallback Mode)",
        "",
        "## Attendees",
        "1. Attendees – Speaker 1 (Inferred)",
        "",
        "## Agenda",
        "- Discuss transcript content and extract key notes",
        "",
        "## Discussion Points",
        "### 1. Main Topics Captured"
    ]
    
    if topics:
        mom_lines.append(f"- Focus topics include: {', '.join(topics)}")
    mom_lines.append("- Discussed key segments of the meeting conversation.")
    
    mom_lines.extend([
        "",
        "## Action Items",
        "",
        "| Sl No | Task | Assigned To | Deadline | Status |",
        "|------|------|-------------|----------|--------|"
    ])
    
    if action_items:
        for idx, act in enumerate(action_items, 1):
            clean_act = act.replace("|", "\\|").replace("\n", " ")
            mom_lines.append(f"| {idx} | {clean_act} | Inferred Speaker | DD/MM/YYYY | Pending |")
    else:
        mom_lines.append("| 1 | Review transcript details | All | DD/MM/YYYY | Pending |")
        
    mom_lines.append("")
    mom_lines.append("## Key Decisions Taken")
    if decisions:
        for dec in decisions:
            mom_lines.append(f"- {dec}")
    else:
        mom_lines.append("- Captured transcription and processed summary.")
        
    mom_lines.extend([
        "",
        "## Risks / Blockers",
        "- None detected in fallback mode.",
        "",
        "## Next Meeting",
        "- **Date:** Unknown",
        "- **Time:** Unknown",
        "- **Agenda:** Follow-up review",
        "",
        "---",
        "**Meeting Ended At:** Unknown"
    ])
    
    mom_markdown = "\n".join(mom_lines)
    
    # Format Fallback MoM Summary markdown
    sum_lines = [
        "# MoM Summary",
        "",
        f"- Meeting held on: {datetime.now().strftime('%d/%m/%Y')}",
        f"- Main discussion: Key topics discussed include {', '.join(topics[:3]) if topics else 'transcript details'}.",
        "- Key decisions:"
    ]
    if decisions:
        for dec in decisions[:3]:
            sum_lines.append(f"  - {dec}")
    else:
        sum_lines.append("  - Captured discussion detail.")
        
    sum_lines.append("- Action items:")
    if action_items:
        for act in action_items[:3]:
            sum_lines.append(f"  - {act} → Assigned to Inferred Speaker")
    else:
        sum_lines.append("  - Review transcript details → Assigned to All")
        
    sum_lines.append("- Deadlines:")
    if action_items:
        for idx, act in enumerate(action_items[:3], 1):
            sum_lines.append(f"  - Task {idx} → DD/MM/YYYY")
    else:
        sum_lines.append("  - Task 1 → DD/MM/YYYY")
        
    sum_lines.extend([
        "- Next meeting scheduled on: Unknown"
    ])
    
    summary_markdown = "\n".join(sum_lines)
    
    return {
        "mom_markdown": mom_markdown,
        "summary_markdown": summary_markdown,
        "word_count": word_count,
        "estimated_duration_min": duration_min
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_summary(text: str, num_sentences: int = 5) -> str:
    """Abstractive summary with TF-IDF fallback (legacy helper)."""
    res = extract_mom(text)
    return res["summary_markdown"]


def extract_mom(text: str) -> dict:
    """Generate structured Minutes of Meeting (MoM) and Summary using Qwen-0.5B."""
    words = text.split() if text else []
    word_count = len(words)
    duration_min = max(1, round(word_count / 130))

    if not text or len(text.strip()) < 60:
        return {
            "mom_markdown": "# MINUTES OF MEETING (MoM)\n\nTranscription too short to summarize.",
            "summary_markdown": "# MoM Summary\n\nTranscription too short to summarize.",
            "word_count": word_count,
            "estimated_duration_min": duration_min,
        }

    pipe = _get_pipeline()
    if pipe is None:
        return _extractive_fallback_mom(text, word_count, duration_min)

    prompt_instruction = (
        "Generate a Minutes of Meeting (MoM) and MoM Summary from the raw transcript. "
        "Format them exactly using the markdown templates below, replacing the bracketed instructions "
        "with actual extracted information from the transcript. If details are not available, leave them blank or use N/A. "
        "Do not output introductory or concluding conversational text. "
        "Generate ONLY the markdown content, separating the MoM Summary section with the '# MoM Summary' header.\n\n"
        "Here are the templates you MUST use:\n\n"
        "# MINUTES OF MEETING (MoM)\n\n"
        "## Meeting Details\n"
        "- **Project/Team Name:** [Extract project or team name if mentioned, else leave blank]\n"
        "- **Meeting Title:** [Extract meeting title if mentioned, else leave blank]\n"
        "- **Date:** [Extract date if mentioned, else leave blank]\n"
        "- **Time:** [Extract time if mentioned, else leave blank]\n"
        "- **Venue/Platform:** [Extract venue or platform if mentioned, else leave blank]\n"
        "- **Meeting Conducted By:** [Extract conductor name if mentioned, else leave blank]\n"
        "- **Minutes Prepared By:** [Extract scribe name if mentioned, else leave blank]\n\n"
        "## Attendees\n"
        "1. Name - Role (Extract list of speakers and roles if mentioned, else list unknown)\n\n"
        "## Agenda\n"
        "- Agenda Point (Extract agenda points from discussion)\n\n"
        "## Discussion Points\n"
        "### 1. Topic Name\n"
        "- Discussion details\n"
        "- Key inputs shared\n"
        "- Decisions taken\n\n"
        "### 2. Topic Name\n"
        "- Discussion details\n"
        "- Concerns/issues raised\n"
        "- Final conclusion\n\n"
        "## Action Items\n\n"
        "| Sl No | Task | Assigned To | Deadline | Status |\n"
        "|------|------|-------------|----------|--------|\n"
        "| 1 | Task description | Name | DD/MM/YYYY | Pending |\n"
        "| 2 | Task description | Name | DD/MM/YYYY | In Progress |\n\n"
        "## Key Decisions Taken\n"
        "- Decision 1\n"
        "- Decision 2\n\n"
        "## Risks / Blockers\n"
        "- Risk or blocker description (if mentioned, else list None)\n"
        "- Dependency details (if mentioned, else list None)\n\n"
        "## Next Meeting\n"
        "- **Date:** [Extract date if mentioned, else leave blank]\n"
        "- **Time:** [Extract time if mentioned, else leave blank]\n"
        "- **Agenda:** [Extract agenda if mentioned, else leave blank]\n\n"
        "---\n"
        "**Meeting Ended At:** [Extract end time if mentioned, else leave blank]\n\n"
        "# MoM Summary\n\n"
        "- Meeting held on: [Date]\n"
        "- Main discussion: [Short discussion topic]\n"
        "- Key decisions:\n"
        "  - Decision 1\n"
        "  - Decision 2\n"
        "- Action items:\n"
        "  - [Task] → Assigned to [Name]\n"
        "- Deadlines:\n"
        "  - Task 1 → DD/MM/YYYY\n"
        "- Next meeting scheduled on: [Date/Time]"
    )

    messages = [
        {
            "role": "system",
            "content": "You are a professional meeting assistant that extracts structured minutes of meeting (MoM) and summaries in markdown format."
        },
        {
            "role": "user",
            "content": f"{prompt_instruction}\n\nRaw Transcription:\n{text}"
        }
    ]

    try:
        # Limit prompt text to ~20,000 words to avoid token limits
        max_prompt_words = 20000
        if len(words) > max_prompt_words:
            truncated_text = " ".join(words[:max_prompt_words])
            messages[1]["content"] = f"{prompt_instruction}\n\nRaw Transcription (Truncated):\n{truncated_text}"

        print("[Summarizer] Generating MoM and Summary with Qwen...")
        res = pipe(messages, max_new_tokens=1500, do_sample=False)
        generated = res[0]['generated_text'][-1]['content'].strip()
        print("[Summarizer] Generation complete.")

        # Split into MoM and MoM Summary
        parts = generated.split("# MoM Summary")
        if len(parts) > 1:
            mom_markdown = parts[0].strip()
            summary_markdown = "# MoM Summary\n\n" + parts[1].strip()
        else:
            # Try case-insensitive split
            idx = generated.lower().find("# mom summary")
            if idx != -1:
                mom_markdown = generated[:idx].strip()
                summary_markdown = generated[idx:].strip()
            else:
                mom_markdown = generated
                summary_markdown = "# MoM Summary\n\n(Generated together with MoM above)"

        return {
            "mom_markdown": mom_markdown,
            "summary_markdown": summary_markdown,
            "word_count": word_count,
            "estimated_duration_min": duration_min
        }
    except Exception as e:
        print(f"[Summarizer] Error during generation: {e}. Using TF-IDF fallback.")
        return _extractive_fallback_mom(text, word_count, duration_min)


if __name__ == "__main__":
    sample = """
    We had a meeting today to discuss the new project timeline.
    John suggested that we should start by building a prototype first.
    Everyone agreed to this approach after a long discussion.
    We decided to use React for the frontend and FastAPI for the backend.
    Sarah needs to complete the database schema by Friday.
    Mark will contact the design team to get the initial UI assets.
    The conclusion is that we are on track for the first milestone.
    We also need to set up the CI/CD pipeline before next week.
    The team agreed that daily standups will be at 9am going forward.
    The budget for the first phase was approved at fifty thousand dollars.
    We confirmed that the cloud infrastructure will be hosted on AWS.
    The QA team should begin writing test cases once the prototype is ready.
    """
    import json
    print(json.dumps(extract_mom(sample), indent=2))
