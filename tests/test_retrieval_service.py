"""Retrieval service unit tests."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from core.config import Settings
from services.analyzers.legal_knowledge_provider import LegalKnowledgeProvider
from services.analyzers.retrieval_service import RetrievalService
from services.rag.knowledge_index import KnowledgeVectorIndex


class FakeEmbeddingProvider:
    def __init__(self, vectors: dict[str, list[float]], available: bool = True) -> None:
        self.model_name = 'fake-embedding-model'
        self._vectors = {key: np.asarray(value, dtype=np.float32) for key, value in vectors.items()}
        self._available = available

    @property
    def available(self) -> bool:
        return self._available

    @property
    def error_message(self) -> str | None:
        return None if self._available else 'fake provider unavailable'

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return np.asarray([self._vectors[text] for text in texts], dtype=np.float32)

    def embed_query(self, text: str) -> np.ndarray:
        return np.asarray(self._vectors[text], dtype=np.float32)


class FailingEmbeddingProvider(FakeEmbeddingProvider):
    def __init__(self) -> None:
        super().__init__({}, available=False)

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        raise RuntimeError('provider unavailable')

    def embed_query(self, text: str) -> np.ndarray:
        raise RuntimeError('provider unavailable')


def create_provider_with_temp_knowledge(tmp_path: Path) -> LegalKnowledgeProvider:
    payload = [
        {
            'id': 'knowledge_001',
            'category': 'general_contract_review',
            'risk_type': 'unilateral_termination',
            'title': '单方解除权限制',
            'content': '解除权一般应与重大违约、法定解除情形或明确约定的触发条件挂钩。',
            'source': '合同风险审查规则',
            'keywords': ['单方解除', '随时解除'],
            'jurisdiction': 'CN',
            'updated_at': '2026-03-28',
        },
        {
            'id': 'knowledge_002',
            'category': 'general_contract_review',
            'risk_type': 'biased_dispute_resolution',
            'title': '争议管辖公平性',
            'content': '争议解决条款不宜以显著增加一方诉讼成本的方式设定管辖地点。',
            'source': '诉讼与仲裁条款审查要点',
            'keywords': ['甲方所在地法院', '仲裁'],
            'jurisdiction': 'CN',
            'updated_at': '2026-03-28',
        },
    ]
    path = tmp_path / 'knowledge_base.json'
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    return LegalKnowledgeProvider(path)


def test_retrieval_service_returns_relevant_snippets() -> None:
    settings = Settings()
    provider = LegalKnowledgeProvider(settings.knowledge_base_path)
    service = RetrievalService(provider, top_k=2)

    clause_text = '甲方有权在任何时候单方解除本合同，且无需承担任何责任。'
    snippets = service.retrieve('unilateral_termination', clause_text)

    assert len(snippets) == 2
    assert snippets[0].risk_type == 'unilateral_termination'
    assert any('解除' in keyword for keyword in snippets[0].keywords)


def test_retrieval_service_favors_matching_risk_type() -> None:
    settings = Settings()
    provider = LegalKnowledgeProvider(settings.knowledge_base_path)
    service = RetrievalService(provider, top_k=2)

    clause_text = '因本合同发生争议时，仅可向甲方所在地人民法院起诉。'
    snippets = service.retrieve('biased_dispute_resolution', clause_text)

    assert snippets
    assert snippets[0].risk_type == 'biased_dispute_resolution'


def test_retrieval_service_supports_new_rule_types() -> None:
    settings = Settings()
    provider = LegalKnowledgeProvider(settings.knowledge_base_path)
    service = RetrievalService(provider, top_k=2)

    clause_text = '合同到期后自动续约一年，如乙方未提出异议则默认续约。'
    snippets = service.retrieve('auto_renewal_trap', clause_text)

    assert snippets
    assert snippets[0].risk_type == 'auto_renewal_trap'
    assert '续约' in snippets[0].content


def test_vector_index_is_persisted_and_reused(tmp_path: Path) -> None:
    provider = create_provider_with_temp_knowledge(tmp_path)
    texts = [
        'general_contract_review unilateral_termination 单方解除权限制 解除权一般应与重大违约、法定解除情形或明确约定的触发条件挂钩。 合同风险审查规则 单方解除 随时解除 CN',
        'general_contract_review biased_dispute_resolution 争议管辖公平性 争议解决条款不宜以显著增加一方诉讼成本的方式设定管辖地点。 诉讼与仲裁条款审查要点 甲方所在地法院 仲裁 CN',
        '甲方可以随时终止合作',
    ]
    embedding_provider = FakeEmbeddingProvider(
        {
            texts[0]: [1.0, 0.0],
            texts[1]: [0.0, 1.0],
            texts[2]: [1.0, 0.0],
        }
    )

    index = KnowledgeVectorIndex(tmp_path / 'rag', embedding_provider)
    index.build_or_load(provider.get_all())

    assert (tmp_path / 'rag' / 'knowledge_embeddings.npy').exists()
    assert (tmp_path / 'rag' / 'knowledge_index.json').exists()
    assert index.available

    second_index = KnowledgeVectorIndex(tmp_path / 'rag', embedding_provider)
    second_index.build_or_load(provider.get_all())
    scores = second_index.rank(texts[2], provider.get_all())

    assert scores['knowledge_001'] > scores['knowledge_002']


def test_retrieval_service_uses_vector_scores_when_available(tmp_path: Path) -> None:
    provider = create_provider_with_temp_knowledge(tmp_path)
    query = '甲方可以随时终止合作'
    texts = [
        'general_contract_review unilateral_termination 单方解除权限制 解除权一般应与重大违约、法定解除情形或明确约定的触发条件挂钩。 合同风险审查规则 单方解除 随时解除 CN',
        'general_contract_review biased_dispute_resolution 争议管辖公平性 争议解决条款不宜以显著增加一方诉讼成本的方式设定管辖地点。 诉讼与仲裁条款审查要点 甲方所在地法院 仲裁 CN',
        query,
    ]
    embedding_provider = FakeEmbeddingProvider(
        {
            texts[0]: [1.0, 0.0],
            texts[1]: [0.0, 1.0],
            texts[2]: [1.0, 0.0],
        }
    )
    index = KnowledgeVectorIndex(tmp_path / 'rag', embedding_provider)
    service = RetrievalService(
        provider,
        top_k=1,
        retrieval_mode='vector_with_lexical_fallback',
        vector_index=index,
    )

    snippets = service.retrieve('unilateral_termination', query)

    assert snippets[0].id == 'knowledge_001'


def test_retrieval_service_falls_back_to_lexical_when_embedding_unavailable(tmp_path: Path) -> None:
    provider = create_provider_with_temp_knowledge(tmp_path)
    index = KnowledgeVectorIndex(tmp_path / 'rag', FailingEmbeddingProvider())
    service = RetrievalService(
        provider,
        top_k=1,
        retrieval_mode='vector_with_lexical_fallback',
        vector_index=index,
    )

    snippets = service.retrieve('biased_dispute_resolution', '仅可向甲方所在地人民法院提起诉讼。')

    assert snippets[0].risk_type == 'biased_dispute_resolution'


def test_retrieval_service_reports_vector_mode_when_index_available(tmp_path: Path) -> None:
    provider = create_provider_with_temp_knowledge(tmp_path)
    query = '甲方可以随时终止合作'
    texts = [
        'general_contract_review unilateral_termination 单方解除权限制 解除权一般应与重大违约、法定解除情形或明确约定的触发条件挂钩。 合同风险审查规则 单方解除 随时解除 CN',
        'general_contract_review biased_dispute_resolution 争议管辖公平性 争议解决条款不宜以显著增加一方诉讼成本的方式设定管辖地点。 诉讼与仲裁条款审查要点 甲方所在地法院 仲裁 CN',
        query,
    ]
    embedding_provider = FakeEmbeddingProvider(
        {
            texts[0]: [1.0, 0.0],
            texts[1]: [0.0, 1.0],
            texts[2]: [1.0, 0.0],
        }
    )
    index = KnowledgeVectorIndex(tmp_path / 'rag', embedding_provider)
    service = RetrievalService(provider, top_k=1, retrieval_mode='vector_with_lexical_fallback', vector_index=index)

    assert service.using_vector_retrieval is True
    assert 'vector retrieval enabled' in service.status_message


def test_retrieval_service_reports_lexical_fallback_when_index_unavailable(tmp_path: Path) -> None:
    provider = create_provider_with_temp_knowledge(tmp_path)
    index = KnowledgeVectorIndex(tmp_path / 'rag', FailingEmbeddingProvider())
    service = RetrievalService(provider, top_k=1, retrieval_mode='vector_with_lexical_fallback', vector_index=index)

    assert service.using_vector_retrieval is False
    assert 'lexical fallback only' in service.status_message
