"""
Veridian — Follow-up Mode
--------------------------
Takes the founder's answers to Veridian's DD questions
and re-scores the report with updated context.

Returns an updated report with:
- Revised scores per section
- Delta from original scores
- New recommendation based on answers
"""

import os
import json
import re
from loguru import logger


FOLLOWUP_PROMPT = """You are Veridian, an expert VC analyst conducting follow-up due diligence.

You previously generated a due diligence report on a company. The founder has now answered your questions.
Your job is to:
1. Assess how well their answers address the concerns you raised
2. Update the scores for each section based on new information
3. Update the recommendation

ORIGINAL REPORT SUMMARY:
Company: {company_name}
Original Verdict: {verdict}
Original Overall Score: {overall_score}/10

Original Scores:
- Market: {market_score}/10
- Team: {team_score}/10  
- Product: {product_score}/10
- Traction: {traction_score}/10

Original Questions Asked:
{questions}

FOUNDER'S ANSWERS:
{answers}

Based on these answers, provide an updated assessment in JSON only:
{{
  "answer_quality": "STRONG" | "ADEQUATE" | "WEAK" | "EVASIVE",
  "answer_quality_reasoning": "string — overall assessment of how well they answered",
  "updated_scores": {{
    "market": 1-10,
    "team": 1-10,
    "product": 1-10,
    "traction": 1-10,
    "overall": 1-10
  }},
  "score_deltas": {{
    "market": -3 to +3,
    "team": -3 to +3,
    "product": -3 to +3,
    "traction": -3 to +3,
    "overall": -3 to +3
  }},
  "updated_verdict": "INVEST" | "WATCH" | "PASS",
  "verdict_changed": true | false,
  "key_insights": ["string — important things learned from their answers"],
  "remaining_concerns": ["string — things still not resolved"],
  "new_questions": ["string — follow-up questions raised by their answers"],
  "updated_recommendation": "string — revised recommendation based on answers"
}}

JSON only, no preamble. Be honest — if their answers raised new red flags, say so.
Score deltas should be positive if answers improved your view, negative if they worsened it."""


def run_followup(
    original_report: dict,
    founder_answers: str,
) -> dict:
    """
    Re-score a report based on founder answers.

    Args:
        original_report: The original DD report dict
        founder_answers: Free text of founder's answers

    Returns:
        Dict with updated scores, deltas, and recommendation
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"success": False, "error": "No API key"}

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
    except ImportError:
        return {"success": False, "error": "google-generativeai not installed"}

    sections = original_report.get("sections", {})
    questions = original_report.get("sections", {}).get("questions_to_ask", [])

    prompt = FOLLOWUP_PROMPT.format(
        company_name=original_report.get("company_name", "Unknown"),
        verdict=original_report.get("verdict", "WATCH"),
        overall_score=original_report.get("overall_score", 0),
        market_score=sections.get("market", {}).get("score", 0),
        team_score=sections.get("team", {}).get("score", 0),
        product_score=sections.get("product", {}).get("score", 0),
        traction_score=sections.get("traction", {}).get("score", 0),
        questions="\n".join(f"- {q}" for q in questions) or "No specific questions recorded",
        answers=founder_answers[:3000],
    )

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=1500,
            ),
        )
        raw = response.text.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"^```\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        result = json.loads(raw)
        logger.success(f"Follow-up complete: verdict={result.get('updated_verdict')}, changed={result.get('verdict_changed')}")
        return {"success": True, "followup": result}

    except json.JSONDecodeError as e:
        return {"success": False, "error": f"JSON parse error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
