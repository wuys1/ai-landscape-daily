from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from ai_landscape_daily.models import Signal

AI_KEYWORDS = {
    "ai", "agent", "agents", "llm", "model", "models", "openai", "gemini", "claude",
    "inference", "multimodal", "machine learning", "deep learning", "neural", "arxiv",
    "chip", "gpu", "大模型", "人工智能", "推理", "智能体", "多模态", "模型",
}

TOPIC_RULES = [
    ("AI 智能体与工作流", {"agent", "agents", "智能体", "workflow", "tool use"}),
    ("大模型与推理能力", {"llm", "large language", "model", "models", "大模型", "reasoning"}),
    ("多模态与视频生成", {"multimodal", "video", "vision", "多模态"}),
    ("AI 基础设施与芯片", {"inference", "chip", "gpu", "accelerator", "推理", "降本"}),
    ("开源模型与开发者工具", {"open model", "open-source", "huggingface", "compact"}),
    ("AI 编程与软件工程", {"codex", "coding", "developer", "software", "代码"}),
    ("企业应用与生产力", {"enterprise", "productivity", "workspace", "work", "职场", "企业"}),
    ("科学、医疗与教育应用", {"medical", "health", "science", "education", "tutor", "医疗", "教育"}),
    ("安全、治理与政策", {"safety", "policy", "governance", "security", "standards", "安全", "治理"}),
    ("投融资与产业竞争", {"funding", "investment", "acquire", "startup", "融资", "收购"}),
]

CANONICAL_TOPICS = [
    "AI 智能体与工作流",
    "大模型与推理能力",
    "多模态与视频生成",
    "AI 基础设施与芯片",
    "开源模型与开发者工具",
    "AI 编程与软件工程",
    "企业应用与生产力",
    "科学、医疗与教育应用",
    "安全、治理与政策",
    "投融资与产业竞争",
    "数据、搜索与内容生态",
    "机器人与具身智能",
]

TOPIC_HINTS = {
    "agent": "AI 智能体与工作流",
    "workflow": "AI 智能体与工作流",
    "llm": "大模型与推理能力",
    "reason": "大模型与推理能力",
    "model": "大模型与推理能力",
    "multimodal": "多模态与视频生成",
    "video": "多模态与视频生成",
    "chip": "AI 基础设施与芯片",
    "inference": "AI 基础设施与芯片",
    "open": "开源模型与开发者工具",
    "github": "开源模型与开发者工具",
    "codex": "AI 编程与软件工程",
    "coding": "AI 编程与软件工程",
    "enterprise": "企业应用与生产力",
    "medical": "科学、医疗与教育应用",
    "education": "科学、医疗与教育应用",
    "policy": "安全、治理与政策",
    "safety": "安全、治理与政策",
    "fund": "投融资与产业竞争",
    "startup": "投融资与产业竞争",
    "search": "数据、搜索与内容生态",
    "robot": "机器人与具身智能",
    "智能体": "AI 智能体与工作流",
    "大模型": "大模型与推理能力",
    "多模态": "多模态与视频生成",
    "芯片": "AI 基础设施与芯片",
    "开源": "开源模型与开发者工具",
    "编程": "AI 编程与软件工程",
    "企业": "企业应用与生产力",
    "医疗": "科学、医疗与教育应用",
    "治理": "安全、治理与政策",
    "融资": "投融资与产业竞争",
    "搜索": "数据、搜索与内容生态",
    "机器人": "机器人与具身智能",
}


class ExtractionPayload(BaseModel):
    topics: list[str] = Field(min_length=1)
    entities: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    signal_type: str = "news"
    summary: str
    contribution: str
    confidence: float = Field(default=0.6, ge=0, le=1)


def is_ai_relevant(row: sqlite3.Row) -> bool:
    text = f"{row['title']} {row['summary']} {row['tags_json']}".lower()
    return any(keyword in text for keyword in AI_KEYWORDS)


def extract_signals(
    rows: list[sqlite3.Row],
    llm_config: dict[str, str] | None = None,
    log: callable | None = None,
) -> list[Signal]:
    signals: list[Signal] = []
    eligible_rows = [row for row in rows if is_ai_relevant(row)]
    if log:
        mode = "LLM" if _llm_enabled(llm_config) else "rules"
        log(f"Extracting signals from {len(eligible_rows)} AI-relevant items using {mode}.")
    for index, row in enumerate(eligible_rows, start=1):
        if log:
            log(f"Extracting item {index}/{len(eligible_rows)}: {row['title'][:80]}")
        try:
            payload_data = _extract_with_llm(row, llm_config) if _llm_enabled(llm_config) else _extract_payload(row)
            payload_data = _normalize_payload_data(payload_data, row)
            payload = ExtractionPayload(**payload_data)
            payload.topics = [_canonical_topic(payload.topics[0])]
        except ValidationError:
            payload = ExtractionPayload(
                topics=["数据、搜索与内容生态"],
                entities=[],
                tags=["ai"],
                signal_type="news",
                summary=(row["summary"] or row["title"])[:240],
                contribution="Provides an AI-related signal for the daily landscape.",
                confidence=0.45,
            )
            if log:
                log(f"Schema validation failed for item {index}; used fallback extraction.")
        except Exception as exc:
            payload = ExtractionPayload(**_extract_payload(row))
            payload.topics = [_canonical_topic(payload.topics[0])]
            if log:
                log(f"LLM extraction failed for item {index}: {exc}. Used fallback extraction.")
        for topic in payload.topics:
            signals.append(
                Signal(
                    item_id=int(row["id"]),
                    topic=topic,
                    entities=payload.entities,
                    tags=payload.tags,
                    signal_type=payload.signal_type,
                    summary=payload.summary,
                    contribution=payload.contribution,
                    confidence=payload.confidence,
                )
            )
    return signals


def _llm_enabled(llm_config: dict[str, str] | None) -> bool:
    return bool(llm_config and llm_config.get("base_url") and llm_config.get("api_key") and llm_config.get("model"))


def _extract_with_llm(row: sqlite3.Row, llm_config: dict[str, str] | None) -> dict[str, Any]:
    if not llm_config:
        return _extract_payload(row)
    prompt = {
        "title": row["title"],
        "summary": row["summary"],
        "source_channel": row["source_channel"],
        "source_name": row["source_name"],
        "tags": _json_list(row["tags_json"]),
        "topic_taxonomy": CANONICAL_TOPICS,
        "instructions": (
            "Return JSON only with keys: topics, entities, tags, signal_type, summary, "
            "contribution, confidence. Choose exactly 1 topic from topic_taxonomy. "
            "summary and contribution must be written in concise Simplified Chinese. "
            "Keep proper nouns, product names, model names, and paper names in their original language. "
            "tags should be short Chinese labels unless they are proper nouns. "
            "confidence must be between 0 and 1."
        ),
    }
    timeout_seconds = float(llm_config.get("timeout_seconds", "15"))
    timeout = httpx.Timeout(timeout_seconds, connect=10.0, read=timeout_seconds, write=10.0, pool=5.0)
    response = httpx.post(
        f"{llm_config['base_url']}/chat/completions",
        headers={
            "Authorization": f"Bearer {llm_config['api_key']}",
            "Content-Type": "application/json",
        },
        json={
            "model": llm_config["model"],
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "你是 AI 行业日报编辑，负责把多语种信息源整理成中文日报信号。"
                        "只返回严格 JSON，不要解释。"
                    ),
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            "temperature": 0.2,
            "max_tokens": 700,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return json.loads(_strip_json_fence(content))


def _normalize_payload_data(payload: dict[str, Any], row: sqlite3.Row) -> dict[str, Any]:
    normalized = dict(payload)
    topics = normalized.get("topics") or normalized.get("topic") or []
    if isinstance(topics, str):
        topics = [topics]
    normalized["topics"] = topics or _extract_payload(row)["topics"]
    for key in ("entities", "tags"):
        value = normalized.get(key, [])
        if isinstance(value, str):
            value = [value]
        normalized[key] = value or []
    normalized["signal_type"] = str(normalized.get("signal_type") or "news")
    normalized["summary"] = str(normalized.get("summary") or _fallback_summary(row, row["summary"]))
    normalized["contribution"] = str(
        normalized.get("contribution")
        or f"来自 {row['source_name']} 的信号，为今日 AI 态势提供补充证据。"
    )
    try:
        normalized["confidence"] = float(normalized.get("confidence", 0.6))
    except (TypeError, ValueError):
        normalized["confidence"] = 0.6
    return normalized


def _strip_json_fence(content: str) -> str:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    return content


def _extract_payload(row: sqlite3.Row) -> dict:
    text = f"{row['title']} {row['summary']}".lower()
    topics = [name for name, keywords in TOPIC_RULES if any(keyword in text for keyword in keywords)]
    if not topics:
        topics = ["数据、搜索与内容生态"]
    tags = list(dict.fromkeys(_json_list(row["tags_json"]) + [topic.lower().replace(" ", "-") for topic in topics]))[:6]
    entities = _entities(row["title"])
    signal_type = "paper" if row["source_channel"] == "papers" else "repo" if row["source_channel"] == "github" else "announcement" if row["source_channel"] == "official" else "news"
    summary = row["summary"] or row["title"]
    contribution = f"来自 {row['source_name']} 的信号，为「{topics[0]}」提供了新的观察证据。"
    return {
        "topics": topics,
        "entities": entities,
        "tags": tags,
        "signal_type": signal_type,
        "summary": _fallback_summary(row, summary),
        "contribution": contribution,
        "confidence": 0.78 if topics != ["AI Industry"] else 0.55,
    }


def _canonical_topic(topic: str) -> str:
    if topic in CANONICAL_TOPICS:
        return topic
    lowered = topic.lower()
    for hint, canonical in TOPIC_HINTS.items():
        if hint in lowered or hint in topic:
            return canonical
    return "数据、搜索与内容生态"


def _fallback_summary(row: sqlite3.Row, summary: str) -> str:
    cleaned = re.sub(r"\s+", " ", summary or row["title"]).strip()[:260]
    if re.search(r"[\u4e00-\u9fff]", cleaned):
        return cleaned
    return f"{row['source_name']} 发布相关动态：{cleaned}"


def _json_list(value: str) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return [str(item) for item in parsed if str(item).strip()]


def _entities(title: str) -> list[str]:
    words = re.findall(r"\b[A-Z][A-Za-z0-9-]{2,}\b", title)
    return [entity for entity, _ in Counter(words).most_common(5)]
