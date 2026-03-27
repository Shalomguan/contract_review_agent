"""
审查记录检索
"""
from datetime import datetime
from typing import List, Optional, Dict
from .db import ReviewDatabase, ReviewRecord


class ReviewSearch:
    """审查记录检索器"""

    def __init__(self, db: Optional[ReviewDatabase] = None):
        self.db = db or ReviewDatabase()

    def search(self, query: str, filters: Optional[Dict] = None) -> List[ReviewRecord]:
        """
        全文搜索审查记录

        Args:
            query: 搜索关键词
            filters: 过滤条件

        Returns:
            匹配的记录列表
        """
        filters = filters or {}

        # 获取所有记录并过滤
        records = self.db.get_all_records()

        results = []
        for record in records:
            # 文本匹配
            if query:
                query_lower = query.lower()
                matches = (
                    query_lower in record.file_name.lower() or
                    query_lower in (record.contract_parties or "").lower() or
                    query_lower in (record.notes or "").lower() or
                    any(query_lower in str(r.get('clause_text', '')).lower() for r in record.risks_detail)
                )
                if not matches:
                    continue

            # 应用过滤条件
            if filters.get('file_type') and record.file_type != filters['file_type']:
                continue

            if filters.get('start_date') and record.review_time < filters['start_date']:
                continue

            if filters.get('end_date') and record.review_time > filters['end_date']:
                continue

            if filters.get('risk_level'):
                # 检查是否有指定风险等级的记录
                has_level = any(
                    r.get('level') == filters['risk_level']
                    for r in record.risks_detail
                )
                if not has_level:
                    continue

            if filters.get('min_risk_count') and filters.get('risk_level'):
                count = sum(
                    1 for r in record.risks_detail
                    if r.get('level') == filters['risk_level']
                )
                if count < filters['min_risk_count']:
                    continue

            results.append(record)

        return results

    def get_recent_reviews(self, days: int = 30, limit: int = 10) -> List[ReviewRecord]:
        """
        获取最近的审查记录

        Args:
            days: 最近天数
            limit: 返回数量

        Returns:
            最近的记录列表
        """
        records = self.db.get_all_records(limit=limit * 2)  # 多取一些用于过滤

        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)

        recent = []
        for record in records:
            if record.review_time >= cutoff_date:
                recent.append(record)
                if len(recent) >= limit:
                    break

        return recent

    def get_high_risk_reviews(self, min_red_count: int = 1) -> List[ReviewRecord]:
        """
        获取高风险审查记录

        Args:
            min_red_count: 最少红色风险数量

        Returns:
            高风险记录列表
        """
        records = self.db.get_all_records(limit=500)

        high_risk = []
        for record in records:
            red_count = record.risk_summary.get('red', 0)
            if red_count >= min_red_count:
                high_risk.append(record)

        # 按红色风险数量排序
        high_risk.sort(key=lambda r: r.risk_summary.get('red', 0), reverse=True)

        return high_risk

    def compare_reviews(self, record_ids: List[int]) -> Dict:
        """
        对比多条审查记录

        Args:
            record_ids: 记录ID列表

        Returns:
            对比结果
        """
        records = []
        for rid in record_ids:
            record = self.db.get_record(rid)
            if record:
                records.append(record)

        if not records:
            return {}

        # 统计对比
        comparison = {
            "record_count": len(records),
            "files": [r.file_name for r in records],
            "overall_ratings": [r.overall_rating for r in records],
            "risk_totals": {
                "red": sum(r.risk_summary.get('red', 0) for r in records),
                "yellow": sum(r.risk_summary.get('yellow', 0) for r in records),
                "green": sum(r.risk_summary.get('green', 0) for r in records),
            },
            "common_risk_types": self._find_common_risk_types(records),
        }

        return comparison

    def _find_common_risk_types(self, records: List[ReviewRecord]) -> List[str]:
        """找出共同的常见风险类型"""
        if not records:
            return []

        from collections import Counter

        all_types = []
        for record in records:
            for risk in record.risks_detail:
                all_types.append(risk.get('risk_type', ''))

        type_counts = Counter(all_types)
        return [t for t, c in type_counts.most_common(5) if t]

    def get_trends(self, days: int = 90) -> Dict:
        """
        获取风险趋势统计

        Args:
            days: 统计天数

        Returns:
            趋势数据
        """
        records = self.db.get_all_records(limit=1000)

        from datetime import timedelta
        cutoff_date = datetime.now() - timedelta(days=days)

        # 按日期统计
        daily_stats = {}
        for record in records:
            if record.review_time >= cutoff_date:
                date_key = record.review_time.strftime('%Y-%m-%d')
                if date_key not in daily_stats:
                    daily_stats[date_key] = {"red": 0, "yellow": 0, "green": 0, "count": 0}

                daily_stats[date_key]["red"] += record.risk_summary.get('red', 0)
                daily_stats[date_key]["yellow"] += record.risk_summary.get('yellow', 0)
                daily_stats[date_key]["green"] += record.risk_summary.get('green', 0)
                daily_stats[date_key]["count"] += 1

        return {
            "period_days": days,
            "total_reviews": len([r for r in records if r.review_time >= cutoff_date]),
            "daily_stats": daily_stats
        }
