from __future__ import annotations

from datetime import datetime, timezone

from ai_landscape_daily.collectors.base import CollectionResult, Collector
from ai_landscape_daily.models import SourceItem


class SampleCollector(Collector):
    name = "sample"

    def collect(self) -> CollectionResult:
        now = datetime.now(timezone.utc)
        items = [
            SourceItem("OpenAI releases new agent tooling for enterprise workflows", "https://openai.com/news/agents?utm_source=newsletter", "OpenAI News", "official", now, "New agent APIs focus on tool use, orchestration, and enterprise controls.", tags=["agents", "enterprise"]),
            SourceItem("GitHub project launches fast local LLM agent runtime", "https://github.com/example/local-agent", "GitHub Trending", "github", now, "A developer tool for running local coding and research agents with plugins.", tags=["agents", "llm"], metadata={"stars_hint": 1280}),
            SourceItem("Multimodal model improves long video understanding", "https://arxiv.org/abs/2606.00001", "arXiv", "papers", now, "Paper proposes a benchmark and model architecture for long-context video reasoning.", tags=["cs.CV", "multimodal"]),
            SourceItem("国内大模型厂商发布推理降本方案", "https://www.qbitai.com/example-inference", "量子位", "chinese_media", now, "多家公司围绕推理加速、缓存和模型压缩展开竞争。", tags=["inference", "llm"]),
            SourceItem("Chip startup announces inference accelerator partnership", "https://www.technologyreview.com/example-ai-chip", "MIT Technology Review AI", "industry", now, "The partnership targets lower latency inference for generative AI workloads.", tags=["chip", "inference"]),
            SourceItem("Open model community ships compact reasoning model", "https://huggingface.co/blog/open-reasoning-model", "Industry Blog", "industry", now, "A compact open model focuses on reasoning, eval transparency, and low deployment cost.", tags=["open model", "llm"]),
        ]
        return CollectionResult(items=items, failures=[])
