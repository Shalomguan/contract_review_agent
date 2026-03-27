# Contract Review Risk Agent MVP

涓€涓彲杩愯銆佸彲鎵╁睍銆佸彲娴嬭瘯鐨勫悎鍚屽鏌ラ闄?Agent 鏈€灏忕増鏈€?
褰撳墠鐗堟湰鐩爣锛?
- 鏀寔涓婁紶 `PDF / DOCX / TXT / 鍥剧墖`
- 鎶藉彇鍚堝悓鏂囨湰骞跺垏鍒嗘潯娆?- 浣跨敤鈥滆鍒?+ Prompt 妯℃澘鈥濊瘑鍒珮椋庨櫓鏉℃
- 杈撳嚭缁撴瀯鍖?JSON
- 淇濆瓨鍘嗗彶瀹℃煡璁板綍

褰撳墠涓嶅仛澶嶆潅 RAG锛屽彧淇濈暀娓呮櫚鎵╁睍鎺ュ彛銆?
## 褰撳墠鐩綍

```text
contract_review_agent/
鈹溾攢鈹€ api/                # FastAPI 搴旂敤涓庤矾鐢?鈹溾攢鈹€ core/               # 閰嶇疆涓庝緷璧栬閰?鈹溾攢鈹€ docs/               # 鏋舵瀯璇存槑銆佹牱渚嬪悎鍚屻€丳ostman collection
鈹溾攢鈹€ models/             # 棰嗗煙妯″瀷
鈹溾攢鈹€ repositories/       # 鏁版嵁璁块棶灞?鈹溾攢鈹€ schemas/            # API 杈撳叆杈撳嚭妯″瀷
鈹溾攢鈹€ services/           # 瑙ｆ瀽銆佸垏鍒嗐€佸垎鏋愩€佸瓨鍌?鈹溾攢鈹€ static/             # 鏈€灏忓墠绔〉闈?鈹溾攢鈹€ tests/              # 鍗曞厓娴嬭瘯涓庢帴鍙ｆ祴璇?鈹溾攢鈹€ data/               # 杩愯鏈?SQLite 鏁版嵁
鈹溾攢鈹€ .env.example        # 鐜鍙橀噺妯℃澘
鈹溾攢鈹€ pytest.ini          # pytest 閰嶇疆
鈹溾攢鈹€ main.py             # 鍏煎鍏ュ彛
鈹溾攢鈹€ requirements.txt
鈹斺攢鈹€ README.md
```

## 鏋舵瀯鍒嗗眰

- `api/`
  鏆撮湶 REST API锛屼笉鎵胯浇涓氬姟閫昏緫銆?- `core/`
  绠＄悊閰嶇疆鍜屼緷璧栨敞鍏ャ€?- `models/`
  瀹氫箟 `Clause`銆乣ParsedDocument`銆乣RiskAnalysis`銆乣Review` 绛夐鍩熷璞°€?- `schemas/`
  瀹氫箟 Pydantic 璇锋眰鍝嶅簲妯″瀷銆?- `services/parsers/`
  璐熻矗涓嶅悓鏂囦欢绫诲瀷鐨勬枃鏈娊鍙栥€?- `services/splitters/`
  璐熻矗鍚堝悓鏉℃鍒囧垎銆?- `services/analyzers/`
  璐熻矗瑙勫垯璇嗗埆銆佹硶寰嬬煡璇嗚幏鍙栥€侀闄╁垎鏋愮紪鎺掋€?- `services/llm/`
  褰撳墠浣跨敤妯℃澘鍖栫粨鏋勮緭鍑猴紝鍚庣画鍙浛鎹㈡垚鐪熷疄 LLM Provider銆?- `services/storage/`
  鎻愪緵 SQLite 鍒濆鍖栥€?- `repositories/`
  璐熻矗瀹℃煡璁板綍鎸佷箙鍖栦笌鏌ヨ銆?
## 宸插疄鐜伴闄╃被鍨?
- `unilateral_exemption`
- `unilateral_termination`
- `excessive_liquidated_damages`
- `unilateral_interpretation`
- `one_sided_ip_assignment`
- `biased_dispute_resolution`

椋庨櫓绛夌骇涓ユ牸闄愬畾涓猴細

- `high`
- `medium`
- `low`

## API

### `POST /api/review/upload`

涓婁紶鍚堝悓鏂囦欢骞惰繑鍥炵粨鏋勫寲瀹℃煡缁撴灉銆?
璇锋眰绫诲瀷锛?
- `multipart/form-data`

瀛楁锛?
- `file`

### `POST /api/review/analyze`

鐩存帴鎻愪氦鍚堝悓鏂囨湰銆?
璇锋眰浣擄細

```json
{
  "document_name": "sample_contract.txt",
  "text": "鍚堝悓鏂囨湰鍐呭"
}
```

### `GET /api/review/{review_id}`

鑾峰彇鍗曟潯鍘嗗彶瀹℃煡璁板綍銆?
### `GET /api/reviews`

鑾峰彇鍘嗗彶瀹℃煡鍒楄〃銆?
鏀寔鍙傛暟锛?
- `limit`
- `offset`

## 杩斿洖缁撴瀯

```json
{
  "review_id": "string",
  "document_id": "string",
  "document_name": "string",
  "summary": "string",
  "created_at": "2026-03-27T12:00:00+00:00",
  "risks": [
    {
      "clause_id": "clause_1",
      "clause_title": "绗竴鏉?浠樻瀹夋帓",
      "clause_text": "......",
      "risk_type": "excessive_liquidated_damages",
      "risk_level": "high",
      "risk_reason": "......",
      "impact_analysis": "......",
      "suggestion": "......",
      "replacement_text": "......"
    }
  ]
}
```

## 杩愯鏂瑰紡

瀹夎渚濊禆锛?
```bash
pip install -r requirements.txt
```

濡傛灉闇€瑕佺幆澧冨彉閲忔ā鏉匡紝鍙厛澶嶅埗锛?
```bash
copy .env.example .env
```

鍚姩鏈嶅姟锛?
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

璁块棶鍦板潃锛?
- Swagger: `http://localhost:8000/docs`
- 鏈€灏忓墠绔? `http://localhost:8000/`

## OCR 璇存槑

濡傛灉闇€瑕佽В鏋愬浘鐗囧悎鍚岋紝璇峰畨瑁?Tesseract OCR銆?
Windows 鍙€氳繃鐜鍙橀噺鎸囧畾璺緞锛?
```bash
set CONTRACT_AGENT_TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

## 娴嬭瘯

杩愯鍏ㄩ儴娴嬭瘯锛?
```bash
pytest
```

鎴栵細

```bash
pytest -q
```

褰撳墠宸茶鐩栵細

- 姝ｅ父鏂囨湰鍒嗘瀽
- 姝ｅ父鏂囦欢涓婁紶
- 鍘嗗彶璁板綍鏌ヨ
- 绌烘枃鏈姹?- 绌烘枃浠朵笂浼?- 涓嶆敮鎸佺殑鏂囦欢绫诲瀷
- 鏌ヨ涓嶅瓨鍦ㄧ殑璁板綍

## Postman

浠撳簱宸叉彁渚涘彲鐩存帴瀵煎叆鐨?collection锛?
- `docs/postman_collection.json`

鎺ㄨ崘鍦?Postman 涓厤缃細

- `base_url = http://localhost:8000`
- `review_id` 鐢卞垎鏋愭帴鍙ｈ嚜鍔ㄥ啓鍏?
## 鏍蜂緥鏁版嵁

- 鏍蜂緥鍚堝悓锛歚docs/sample_contract.txt`
- 鏋舵瀯璇存槑锛歚docs/architecture.md`
- Postman collection锛歚docs/postman_collection.json`

## 鍚庣画鎵╁睍

- 鎶?`TemplateLLMClient` 鏇挎崲鎴愮湡瀹炴ā鍨嬭皟鐢?- 鎶?`StaticLegalKnowledgeProvider` 鍗囩骇鎴愭硶瑙勫簱/RAG 妫€绱㈠眰
- 澧炲姞涓讳綋璇嗗埆銆侀噾棰濇娊鍙栥€佹湡闄愭娊鍙?- 澧炲姞 PostgreSQL 鍜屽璞″瓨鍌ㄦ敮鎸?