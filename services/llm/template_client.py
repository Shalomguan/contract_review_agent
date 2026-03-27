"""Deterministic template-based analysis generator."""
from services.llm.base import PromptPayload


class TemplateLLMClient:
    """Fallback structured client that produces stable outputs without external APIs."""

    templates = {
        "unilateral_exemption": {
            "risk_reason": "条款将免责利益单方面分配给一方，可能导致责任失衡，且在故意或重大过失场景下存在无效风险。",
            "impact_analysis": "守约方发生损失后可能难以主张赔偿，合同履约约束力被削弱。",
            "suggestion": "删除绝对免责措辞，仅保留法定免责或经双方书面确认的合理免责范围。",
            "replacement_text": (
                "任何一方违反本合同约定造成对方损失的，应承担相应赔偿责任。"
                "但因不可抗力或经双方书面确认的免责事由造成的损失，可依法部分或全部免责。"
            ),
        },
        "unilateral_termination": {
            "risk_reason": "条款赋予一方过宽的单方解除权，缺少明确触发条件、通知期限和补救机会。",
            "impact_analysis": "另一方可能在已投入成本后被突然解除合作，造成履约和结算风险。",
            "suggestion": "将解除权限定为明确违约或法定情形，并增加提前通知和整改期限。",
            "replacement_text": (
                "任何一方仅在对方发生重大违约且在收到书面通知后十个工作日内未完成整改时，"
                "方可书面解除本合同。解除不影响守约方依法追究违约责任。"
            ),
        },
        "excessive_liquidated_damages": {
            "risk_reason": "违约金或滞纳金比例明显偏高，超出合理补偿范围时存在被调减的风险。",
            "impact_analysis": "违约方可能承担过重付款义务，条款的可执行性和商业可接受性下降。",
            "suggestion": "将违约金调整至与实际损失更匹配的比例，并避免按日叠加过高费率。",
            "replacement_text": (
                "违约方应向守约方支付相当于受影响合同价款 10% 的违约金；"
                "如该金额不足以弥补守约方实际损失，守约方可继续主张超出部分的合理损失。"
            ),
        },
        "unilateral_interpretation": {
            "risk_reason": "条款赋予一方最终解释权，会削弱合同文本的共同约束力和争议解决中立性。",
            "impact_analysis": "解释权被单方控制时，另一方在履约争议中处于被动地位。",
            "suggestion": "删除最终解释权表述，改为通过补充协议或争议解决机制处理理解分歧。",
            "replacement_text": (
                "本合同条款的理解与执行应以双方共同确认的书面约定为准；"
                "如存在分歧，双方应先友好协商，协商不成时按本合同争议解决条款处理。"
            ),
        },
        "one_sided_ip_assignment": {
            "risk_reason": "知识产权归属完全偏向一方，未区分既有成果、委托成果和使用许可范围。",
            "impact_analysis": "成果交付后可能产生权属争议，研发方或委托方的核心权益无法被清晰保护。",
            "suggestion": "按既有知识产权、交付成果及使用许可三类进行拆分约定。",
            "replacement_text": (
                "双方各自享有其在合作前已拥有的知识产权。合作过程中形成的交付成果知识产权"
                "由双方根据项目性质在附件中明确约定；未明确约定的，另一方至少享有为履行本合同所必需的非独占使用权。"
            ),
        },
        "biased_dispute_resolution": {
            "risk_reason": "争议解决地点明显偏向一方，可能提高另一方维权成本并影响程序公平。",
            "impact_analysis": "异地应诉、举证和执行成本上升，商业谈判地位可能失衡。",
            "suggestion": "选择与合同履行地、被告所在地或双方共同认可地点更接近的中立争议解决机制。",
            "replacement_text": (
                "因本合同引起的争议，双方应先友好协商；协商不成的，任一方可向合同履行地"
                "有管辖权的人民法院提起诉讼，或提交双方书面确认的仲裁机构仲裁。"
            ),
        },
    }

    def analyze(self, payload: PromptPayload) -> dict[str, str]:
        """Return structured analysis from deterministic templates."""
        template = self.templates.get(
            payload.risk_type,
            {
                "risk_reason": "该条款存在需要进一步审查的潜在风险。",
                "impact_analysis": "如不调整，可能在履约或争议处理中增加不确定性。",
                "suggestion": "建议由法务或律师结合交易背景补充约束条件和权责边界。",
                "replacement_text": payload.clause_text,
            },
        )
        reference_suffix = ""
        if payload.references:
            reference_suffix = f" 参考提示：{payload.references[0]}"

        return {
            "risk_reason": template["risk_reason"] + reference_suffix,
            "impact_analysis": template["impact_analysis"],
            "suggestion": template["suggestion"],
            "replacement_text": template["replacement_text"],
        }
