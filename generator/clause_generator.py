"""
修改建议生成器
使用MiniMax API生成合同修改建议
"""
import json
from typing import Optional, Dict, List
from dataclasses import dataclass
from config import settings

try:
    from langchain_anthropic import ChatAnthropic
except ImportError:
    ChatAnthropic = None

from rag import Retriever, PromptBuilder


@dataclass
class ClauseSuggestion:
    """条款修改建议"""
    original_clause: str  # 原文
    risk_type: str  # 风险类型
    reason: str  # 修改理由
    suggested_clause: str  # 建议文本
    legal_basis: str  # 法律依据


class ClauseGenerator:
    """合同条款修改建议生成器"""

    def __init__(self):
        self.retriever = Retriever()
        self.prompt_builder = PromptBuilder()
        self._llm = None

    def _get_llm(self):
        """获取LLM实例（懒加载）"""
        if self._llm is None:
            if ChatAnthropic is None:
                raise ImportError("请安装langchain-anthropic: pip install langchain-anthropic")

            # MiniMax API兼容Anthropic格式
            self._llm = ChatAnthropic(
                model=settings.MINIMAX_MODEL,
                anthropic_api_key=settings.MINIMAX_API_KEY,
                base_url=settings.MINIMAX_BASE_URL,
                temperature=0.3
            )
        return self._llm

    def generate_suggestion(self, clause_text: str, risk_type: str,
                           party_info: Optional[str] = None) -> ClauseSuggestion:
        """
        为单个风险条款生成修改建议

        Args:
            clause_text: 风险条款文本
            risk_type: 风险类型
            party_info: 甲方乙方信息

        Returns:
            修改建议
        """
        # 检索相关法律条款
        retrieval_result = self.retriever.retrieve_for_suggestion(clause_text, risk_type)
        retrieved_laws = retrieval_result["formatted_text"]

        # 构建提示词
        prompt = self.prompt_builder.build_suggestion_prompt(
            clause_text=clause_text,
            risk_type=risk_type,
            retrieved_laws=retrieved_laws,
            party_info=party_info
        )

        # 调用LLM生成建议
        try:
            llm = self._get_llm()
            response = llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # 解析响应
            return self._parse_suggestion_response(
                response_text, clause_text, risk_type, retrieved_laws
            )
        except Exception as e:
            # 如果API调用失败，返回基于规则的默认建议
            return self._generate_fallback_suggestion(clause_text, risk_type, retrieved_laws)

    def generate_batch_suggestions(self, risk_clauses: List[Dict]) -> List[ClauseSuggestion]:
        """
        批量生成修改建议

        Args:
            risk_clauses: 风险条款列表，每项包含clause_text和risk_type

        Returns:
            修改建议列表
        """
        suggestions = []
        for item in risk_clauses:
            suggestion = self.generate_suggestion(
                clause_text=item["clause_text"],
                risk_type=item["risk_type"],
                party_info=item.get("party_info")
            )
            suggestions.append(suggestion)

        return suggestions

    def _parse_suggestion_response(self, response: str, original_clause: str,
                                    risk_type: str, legal_basis: str) -> ClauseSuggestion:
        """解析LLM响应"""
        # 尝试提取各部分
        reason = ""
        suggested_clause = ""
        extracted_legal_basis = ""

        lines = response.split('\n')
        current_section = None

        for line in lines:
            line = line.strip()
            if '修改理由' in line:
                current_section = 'reason'
                continue
            elif '示范条款' in line:
                current_section = 'suggestion'
                continue
            elif '法律依据' in line:
                current_section = 'legal'
                continue

            if current_section == 'reason' and line:
                reason += line + " "
            elif current_section == 'suggestion' and line:
                suggested_clause += line + "\n"
            elif current_section == 'legal' and line:
                extracted_legal_basis += line + " "

        # 如果解析失败，使用原始响应
        if not reason and not suggested_clause:
            reason = "该条款存在法律风险，建议修改"
            suggested_clause = response

        return ClauseSuggestion(
            original_clause=original_clause,
            risk_type=risk_type,
            reason=reason.strip(),
            suggested_clause=suggested_clause.strip(),
            legal_basis=extracted_legal_basis.strip() or legal_basis
        )

    def _generate_fallback_suggestion(self, clause_text: str, risk_type: str,
                                       legal_basis: str) -> ClauseSuggestion:
        """生成备用建议（当API不可用时）"""
        fallback_suggestions = {
            "违约金过高": {
                "reason": "违约金金额或计算方式可能违反公平原则，建议调整为合理范围。",
                "suggestion": "违约金条款：任何一方违反本合同约定的，应当向守约方支付合同总金额{}%的违约金。（注：建议违约金比例不超过合同金额的30%）"
            },
            "保密条款不明确": {
                "reason": "保密条款的范围、期限不明确，建议明确约定。",
                "suggestion": "保密条款：双方应对在合作过程中知悉的对方商业秘密负有保密义务。保密期限为合同终止后{}年内。保密信息的使用仅限于本合同约定的目的。"
            },
            "争议解决不利": {
                "reason": "争议解决条款可能对一方不利，建议选择中立机构。",
                "suggestion": "争议解决条款：因本合同引起的任何争议，双方应首先友好协商解决；协商不成的，提交【】仲裁委员会仲裁，仲裁裁决为终局裁决。"
            },
            "责任边界模糊": {
                "reason": "责任边界约定不清晰，建议明确约定。",
                "suggestion": "责任限制条款：任何一方因违反本合同而承担的赔偿责任，以该方在合同项下已收取或应收的实际合同金额为限，但因故意或重大过失造成的损失除外。"
            },
            "终止条款不合理": {
                "reason": "单方面终止权可能损害对方利益，建议增加合理条件。",
                "suggestion": "终止条款：合同的解除需经双方协商一致，并以书面形式通知对方。因一方违约导致合同解除的，守约方有权要求违约方赔偿损失。"
            },
            "支付条款风险": {
                "reason": "支付条款存在不对称风险，建议明确各方义务。",
                "suggestion": "支付条款：买方应按合同约定的时间和方式支付款项。如需变更支付方式，应提前{}日书面通知对方并获得书面同意。"
            },
        }

        fallback = fallback_suggestions.get(risk_type, {
            "reason": "该条款存在法律风险，建议由专业律师审查后修改。",
            "suggestion": "建议委托专业律师根据具体情况拟定修改方案。"
        })

        return ClauseSuggestion(
            original_clause=clause_text,
            risk_type=risk_type,
            reason=fallback["reason"],
            suggested_clause=fallback["suggestion"],
            legal_basis=legal_basis
        )
