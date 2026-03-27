"""
审查记录数据库
使用SQLAlchemy管理SQLite数据库
"""
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path
import json

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker as async_sessionmaker

from config import settings

Base = declarative_base()


class ReviewRecordModel(Base):
    """审查记录模型"""
    __tablename__ = "review_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=True)
    review_time = Column(DateTime, default=datetime.now)
    overall_rating = Column(String(50), nullable=False)
    risk_summary = Column(JSON, nullable=True)  # {"red": 0, "yellow": 0, "green": 0}
    risks_detail = Column(JSON, nullable=True)  # 风险详情列表
    suggestions = Column(JSON, nullable=True)  # 修改建议列表
    contract_parties = Column(String(500), nullable=True)  # 合同当事人
    contract_value = Column(String(100), nullable=True)  # 合同金额
    notes = Column(Text, nullable=True)  # 备注


@dataclass
class ReviewRecord:
    """审查记录数据类"""
    id: int
    file_name: str
    file_type: str
    file_path: Optional[str]
    review_time: datetime
    overall_rating: str
    risk_summary: dict
    risks_detail: List[dict]
    suggestions: List[dict]
    contract_parties: Optional[str]
    contract_value: Optional[str]
    notes: Optional[str]


class ReviewDatabase:
    """审查记录数据库管理"""

    def __init__(self, db_path: Optional[str] = None):
        """
        初始化数据库

        Args:
            db_path: 数据库路径，默认使用配置中的路径
        """
        if db_path is None:
            db_path = settings.DB_PATH

        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # SQLite URL
        self.db_url = f"sqlite:///{db_path}"

        # 创建同步引擎（用于初始化）
        self.engine = create_engine(self.db_url, echo=False)
        Base.metadata.create_all(self.engine)

        # Session factory
        self.Session = sessionmaker(bind=self.engine)

    def add_record(self, record: dict) -> int:
        """
        添加审查记录

        Args:
            record: 记录数据字典

        Returns:
            新记录的ID
        """
        session = self.Session()
        try:
            model = ReviewRecordModel(
                file_name=record.get("file_name", ""),
                file_type=record.get("file_type", ""),
                file_path=record.get("file_path"),
                overall_rating=record.get("overall_rating", "待评估"),
                risk_summary=record.get("risk_summary"),
                risks_detail=record.get("risks_detail"),
                suggestions=record.get("suggestions"),
                contract_parties=record.get("contract_parties"),
                contract_value=record.get("contract_value"),
                notes=record.get("notes")
            )
            session.add(model)
            session.commit()
            return model.id
        finally:
            session.close()

    def get_record(self, record_id: int) -> Optional[ReviewRecord]:
        """获取单条记录"""
        session = self.Session()
        try:
            model = session.query(ReviewRecordModel).filter_by(id=record_id).first()
            if model:
                return self._model_to_record(model)
            return None
        finally:
            session.close()

    def get_all_records(self, limit: int = 100, offset: int = 0) -> List[ReviewRecord]:
        """获取所有记录"""
        session = self.Session()
        try:
            models = session.query(ReviewRecordModel)\
                .order_by(ReviewRecordModel.review_time.desc())\
                .limit(limit)\
                .offset(offset)\
                .all()
            return [self._model_to_record(m) for m in models]
        finally:
            session.close()

    def search_records(self, file_name: Optional[str] = None,
                       contract_type: Optional[str] = None,
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None,
                       risk_level: Optional[str] = None) -> List[ReviewRecord]:
        """
        搜索审查记录

        Args:
            file_name: 文件名（模糊搜索）
            contract_type: 合同类型
            start_date: 开始日期
            end_date: 结束日期
            risk_level: 风险等级（red/yellow/green）

        Returns:
            匹配的记录列表
        """
        session = self.Session()
        try:
            query = session.query(ReviewRecordModel)

            if file_name:
                query = query.filter(ReviewRecordModel.file_name.contains(file_name))

            if contract_type:
                query = query.filter(ReviewRecordModel.file_type == contract_type)

            if start_date:
                query = query.filter(ReviewRecordModel.review_time >= start_date)

            if end_date:
                query = query.filter(ReviewRecordModel.review_time <= end_date)

            if risk_level:
                # 需要在JSON字段中搜索
                query = query.filter(ReviewRecordModel.risk_summary.contains(risk_level))

            models = query.order_by(ReviewRecordModel.review_time.desc()).all()
            return [self._model_to_record(m) for m in models]
        finally:
            session.close()

    def delete_record(self, record_id: int) -> bool:
        """删除记录"""
        session = self.Session()
        try:
            model = session.query(ReviewRecordModel).filter_by(id=record_id).first()
            if model:
                session.delete(model)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_statistics(self) -> dict:
        """获取统计数据"""
        session = self.Session()
        try:
            total = session.query(ReviewRecordModel).count()

            # 统计各风险等级数量
            records = session.query(ReviewRecordModel).all()
            risk_counts = {"red": 0, "yellow": 0, "green": 0}

            for record in records:
                if record.risk_summary:
                    risk_counts["red"] += record.risk_summary.get("red", 0)
                    risk_counts["yellow"] += record.risk_summary.get("yellow", 0)
                    risk_counts["green"] += record.risk_summary.get("green", 0)

            return {
                "total_reviews": total,
                "risk_counts": risk_counts
            }
        finally:
            session.close()

    def _model_to_record(self, model: ReviewRecordModel) -> ReviewRecord:
        """将数据库模型转换为数据类"""
        return ReviewRecord(
            id=model.id,
            file_name=model.file_name,
            file_type=model.file_type,
            file_path=model.file_path,
            review_time=model.review_time,
            overall_rating=model.overall_rating,
            risk_summary=model.risk_summary or {},
            risks_detail=model.risks_detail or [],
            suggestions=model.suggestions or [],
            contract_parties=model.contract_parties,
            contract_value=model.contract_value,
            notes=model.notes
        )
