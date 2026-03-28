"""Deterministic template-based analysis generator."""
from services.llm.base import PromptPayload


class TemplateLLMClient:
    """Fallback structured client that produces stable outputs without external APIs."""

    templates = {
        "unilateral_exemption": {
            "risk_reason": "条款允许一方通过免责表述转移主要违约责任。",
            "impact_analysis": "对方在对象延期、质量缺陷或损失赔偿争议中可能处于明显不利地位。",
            "suggestion": "将免责范围限定为法定不可归责于当事人的情况，并保留违约责任。",
            "replacement_text": "除因不可抗力或对方原因造成的损失外，任何一方对其违约、过错或未履行本合同义务导致的损失仍应承担相应责任。",
        },
        "unilateral_termination": {
            "risk_reason": "条款赋予一方无需理由即可单方解除合同的权利。",
            "impact_analysis": "另一方的履约预期和成本投入缺乏保障，容易造成履约中断或损失难以追偿。",
            "suggestion": "将解除权限定为法定或约定的严重违约情形，并设置合理通知期。",
            "replacement_text": "任何一方仅在对方发生重大违约且在合理催告期内未改正的情况下，方可书面通知解除本合同。",
        },
        "excessive_liquidated_damages": {
            "risk_reason": "条款设置的违约金或滞纳金水平明显偏高。",
            "impact_analysis": "过高的违约金会放大履约风险，也可能在争议中被认定为显失公平。",
            "suggestion": "调整为与实际损失和行业常规相匹配的比例。",
            "replacement_text": "若一方违约，应按实际损失承担违约责任；如约定违约金，其总额以不超过对应合同价款的 10% 为宜。",
        },
        "unilateral_interpretation": {
            "risk_reason": "条款将最终解释权集中赋予一方。",
            "impact_analysis": "在对合同含义存在争议时，另一方难以获得平衡的解释结果。",
            "suggestion": "删除单方最终解释权，改为双方协商不成后按法律规则解释。",
            "replacement_text": "本合同条款的理解与适用由双方本着诚信原则协商确定，协商不成的按照相关法律规定处理。",
        },
        "one_sided_ip_assignment": {
            "risk_reason": "条款将知识产权成果不区分地全部归于一方。",
            "impact_analysis": "可能使实际开发方、供应方或创作方对成果丧失合理权益。",
            "suggestion": "按照既有知识产权、定制化成果和授权范围分层约定。",
            "replacement_text": "各方在本合同签署前已享有的知识产权仍归原权利人所有；对定制化交付成果，可根据付款情况约定所有权或排他授权。",
        },
        "biased_dispute_resolution": {
            "risk_reason": "条款将争议管辖地点明显偏向一方。",
            "impact_analysis": "对方在诉讼或仲裁成本、证据组织和程序参与方面可能处于不利地位。",
            "suggestion": "改为双方协商选定的仲裁机构或被告住所地法院管辖。",
            "replacement_text": "因本合同引起的争议，双方应先行协商；协商不成的，可向被告住所地有管辖权的人民法院提起诉讼。",
        },
        "auto_renewal_trap": {
            "risk_reason": "条款对自动续约的生效条件和退出机制设置偏于严苛。",
            "impact_analysis": "未及时注意就可能进入新的履约周期，增加合同绑定成本。",
            "suggestion": "增加续约前提醒、合理通知期和明确退出窗口。",
            "replacement_text": "合同到期前至少 30 日，双方应以书面形式确认是否续约；未经双方明确同意，本合同不自动顺延。",
        },
        "unilateral_change_right": {
            "risk_reason": "条款赋予一方单方变更价格、规则或履约标准的权利。",
            "impact_analysis": "另一方的成本预期和履约安排可能在无协商的情况下被动变动。",
            "suggestion": "改为双方协商一致后方可变更，并保留对方拒绝或解除权。",
            "replacement_text": "涉及价格、服务内容、规则或履约标准的重大调整，应由双方协商一致并以书面形式确认后生效。",
        },
        "payment_imbalance": {
            "risk_reason": "条款对付款时点、确认依据或预付款比例的设置明显失衡。",
            "impact_analysis": "付款风险会在未完成对价交付时提前集中到一方。",
            "suggestion": "按交付里程碑、双方确认节点或可验证成果设计付款安排。",
            "replacement_text": "价款支付应与实际交付进度、双方确认的验收结果或对账单相挂钩，预付款比例以不超过合同总价的 30% 为宜。",
        },
        "acceptance_unfairness": {
            "risk_reason": "条款将验收结论完全交由一方单方认定或默认成立。",
            "impact_analysis": "另一方可能在缺乏客观标准的情况下承担违约或交付责任。",
            "suggestion": "补充双方可操作的验收标准、验收期限和异议处理机制。",
            "replacement_text": "验收应基于双方确认的交付标准和测试结果进行，甲方应在收到交付物后 5 个工作日内提出书面异议，双方应就异议部分协商处理。",
        },
        "confidentiality_imbalance": {
            "risk_reason": "条款对保密义务的主体、期限或例外范围设置明显失衡。",
            "impact_analysis": "可能使某一方长期承担过度限制，但另一方无对等义务。",
            "suggestion": "明确保密义务适用于双方，并设定合理期限与公开信息等例外情形。",
            "replacement_text": "双方对在履行本合同过程中知悉的商业秘密和未公开信息均负有保密义务，保密期为合同终止后 3 年，但依法应公开或已公知的信息除外。",
        },
        "non_compete_or_exclusivity": {
            "risk_reason": "条款以排他、独家或竞业限制对一方赋予过强绑定。",
            "impact_analysis": "可能导致一方在合作期内无法正常开展其他业务或交易。",
            "suggestion": "限定独家范围、期限、地域和例外情形，并设置合理补偿或退出机制。",
            "replacement_text": "如需约定独家或排他合作，其适用范围应限于明确产品、客户或地域，期限不得超过合理商业期限，且不得禁止与无直接竞争关系的第三方合作。",
        },
        "delivery_or_notice_trap": {
            "risk_reason": "条款将通知或送达的生效标准设置为发出即生效。",
            "impact_analysis": "另一方可能在实际未收悉通知时已承担不利后果。",
            "suggestion": "明确以实际送达、签收或能证明已阅的时点作为生效时点。",
            "replacement_text": "一方向另一方发出的通知，应以快递签收、邮箱回执或双方确认收悉的系统记录作为送达依据。",
        },
        "termination_penalty_unfairness": {
            "risk_reason": "条款对提前解约或终止设置了过高的费用或不对等的责任。",
            "impact_analysis": "可能使一方在商业情况变化时无法合理退出或消化损失。",
            "suggestion": "将解约后果限定为已发生的实际损失或未履行部分的合理对价。",
            "replacement_text": "如一方提前解除或终止合同，只对已发生且可证明的实际损失承担责任，不得要求一次性支付全部未履行期间的费用。",
        },
        "liability_imbalance": {
            "risk_reason": "条款将违约、赔偿或补救责任明显集中给一方。",
            "impact_analysis": "可能造成风险承担与控制能力不匹配，增加履约和争议成本。",
            "suggestion": "按违约行为、过错程度和损失结果对等分配责任。",
            "replacement_text": "双方对各自的违约、过错或侵权行为导致的损失承担相应责任，任何赔偿范围应以实际损失和合理预见为限。",
        },
        "missing_core_terms": {
            "risk_reason": "条款提及了核心事项，但缺少必要的标准、时间或流程要素。",
            "impact_analysis": "在后续履行或结算阶段容易出现理解不一致的争议。",
            "suggestion": "补充可执行的时间节点、验收标准、金额或程序性内容。",
            "replacement_text": "双方应对相关事项的完成标准、时间节点、责任人及异议处理方式作出明确约定。",
        },
    }

    def analyze(self, payload: PromptPayload) -> dict[str, str]:
        """Return structured analysis from deterministic templates."""
        template = self.templates.get(
            payload.risk_type,
            {
                "risk_reason": "条款存在需要进一步复核的风险因素。",
                "impact_analysis": "建议结合实际交易背景、责任分工和行业惯例进行进一步审查。",
                "suggestion": "补充权利义务对等性、标准化程序和可验证的履约要求。",
                "replacement_text": payload.clause_text,
            },
        )

        return {
            "risk_reason": template["risk_reason"],
            "impact_analysis": template["impact_analysis"],
            "suggestion": template["suggestion"],
            "replacement_text": template["replacement_text"],
        }
