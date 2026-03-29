"""Service container assembly."""
from dataclasses import dataclass

from core.config import Settings, get_settings
from core.security import PasswordHasher, TokenManager
from repositories.review_repository import ReviewRepository
from repositories.user_repository import UserRepository
from services.analyzers.legal_knowledge_provider import LegalKnowledgeProvider
from services.auth_service import AuthService
from services.analyzers.prompt_analyzer import PromptAnalyzer
from services.analyzers.retrieval_service import RetrievalService
from services.analyzers.risk_analyzer import RiskAnalyzer
from services.analyzers.rule_engine import RuleEngine
from services.llm.prompt_builder import PromptBuilder
from services.llm.template_client import TemplateLLMClient
from services.parsers.docx_parser import DocxParser
from services.parsers.factory import DocumentParserFactory
from services.parsers.image_parser import ImageParser
from services.parsers.pdf_parser import PdfParser
from services.parsers.text_parser import TextParser
from services.rag.embedding_provider import SentenceTransformerEmbeddingProvider
from services.report_exporter import ReviewExporter
from services.rag.knowledge_index import KnowledgeVectorIndex
from services.review_service import ReviewService
from services.splitters.contract_splitter import ContractSplitter
from services.storage.sqlite_db import SQLiteDatabase


@dataclass(slots=True)
class ApplicationContainer:
    """Top-level application dependencies."""

    settings: Settings
    auth_service: AuthService
    review_service: ReviewService


def build_container(settings: Settings | None = None) -> ApplicationContainer:
    """Build the application service graph."""
    settings = settings or get_settings()
    settings.ensure_directories()

    database = SQLiteDatabase(settings.database_path)
    user_repository = UserRepository(database)
    review_repository = ReviewRepository(database)

    password_hasher = PasswordHasher()
    token_manager = TokenManager(
        secret_key=settings.auth_secret_key,
        ttl_minutes=settings.auth_token_ttl_minutes,
    )
    auth_service = AuthService(
        user_repository=user_repository,
        password_hasher=password_hasher,
        token_manager=token_manager,
    )

    parser_factory = DocumentParserFactory(
        parsers=[
            TextParser(),
            PdfParser(),
            DocxParser(),
            ImageParser(settings=settings),
        ]
    )
    splitter = ContractSplitter()
    rule_engine = RuleEngine()
    knowledge_provider = LegalKnowledgeProvider(settings.knowledge_base_path)
    embedding_provider = SentenceTransformerEmbeddingProvider(
        model_name=settings.embedding_model_name,
        cache_dir=settings.embedding_cache_dir,
        local_files_only=settings.embedding_local_files_only,
    )
    vector_index = KnowledgeVectorIndex(
        index_dir=settings.rag_index_dir,
        embedding_provider=embedding_provider,
        rebuild_on_start=settings.rag_rebuild_on_start,
    )
    retrieval_service = RetrievalService(
        legal_knowledge_provider=knowledge_provider,
        top_k=settings.retrieval_top_k,
        retrieval_mode=settings.retrieval_mode,
        vector_index=vector_index,
    )
    prompt_builder = PromptBuilder()
    llm_client = TemplateLLMClient()
    prompt_analyzer = PromptAnalyzer(prompt_builder=prompt_builder, llm_client=llm_client)
    risk_analyzer = RiskAnalyzer(
        rule_engine=rule_engine,
        retrieval_service=retrieval_service,
        prompt_analyzer=prompt_analyzer,
    )

    review_exporter = ReviewExporter()

    review_service = ReviewService(
        settings=settings,
        parser_factory=parser_factory,
        splitter=splitter,
        risk_analyzer=risk_analyzer,
        review_repository=review_repository,
        review_exporter=review_exporter,
    )

    return ApplicationContainer(settings=settings, auth_service=auth_service, review_service=review_service)
