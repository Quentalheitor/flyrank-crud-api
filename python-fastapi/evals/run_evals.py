import json
import os
import sys
import urllib.error
import urllib.request

API_URL = "http://127.0.0.1:8000/triage"
CASES_PATH = os.path.join(os.path.dirname(__file__), "cases.json")
REQUIRED_KEYS = ["category", "urgency", "difficulty", "suggested_team", "confidence", "reason"]


def evaluate_response(res_data: dict, expected: dict, case_type: str) -> list[str]:
    errors = []

    for key in REQUIRED_KEYS:
        if key not in res_data:
            errors.append(f"Missing required key: '{key}'")

    if errors:
        return errors

    for field in ["category", "urgency", "difficulty", "suggested_team"]:
        expected_val = expected.get(field)
        actual_val = res_data.get(field)
        if actual_val != expected_val:
            errors.append(f"{field}: expected '{expected_val}', got '{actual_val}'")

    conf = res_data.get("confidence")
    if not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
        errors.append(f"confidence: must be float between 0.0 and 1.0, got '{conf}'")
    elif case_type in ("ambiguous_ticket", "unsure_fallback") and conf >= 0.5:
        errors.append(f"confidence: expected < 0.5 for fallback/unsure case, got {conf}")

    reason = res_data.get("reason")
    if not isinstance(reason, str) or len(reason.strip()) == 0:
        errors.append("reason: must be a non-empty string")
    elif len(reason) > 200:
        errors.append(f"reason: exceeds 200 characters ({len(reason)} chars)")

    return errors


def run_evals():
    with open(CASES_PATH, "r", encoding="utf-8") as f:
        cases = json.load(f)

    total = len(cases)
    fully_passed = 0
    failures = []

    print(f"\nEvaluating {total} cases across all 6 schema keys against {API_URL}...\n")

    for i, case in enumerate(cases, 1):
        payload = case["input"]
        expected = case["expected"]
        case_type = case["case_type"]

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            API_URL, data=data, headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=35) as res:
                response_body = json.loads(res.read().decode("utf-8"))
                errors = evaluate_response(response_body, expected, case_type)

                if not errors:
                    print(
                        f"[{i}/{total}] PASS ({case_type}): "
                        f"[{response_body['category']} | {response_body['urgency']} | "
                        f"{response_body['difficulty']} | {response_body['suggested_team']}]"
                    )
                    fully_passed += 1
                else:
                    print(f"[{i}/{total}] FAIL ({case_type})")
                    for err in errors:
                        print(f"       -> {err}")
                    failures.append({
                        "id": payload["id"],
                        "case_type": case_type,
                        "errors": errors,
                        "response": response_body
                    })

        except urllib.error.HTTPError as e:
            err_msg = f"HTTP Error {e.code}: {e.read().decode('utf-8')}"
            print(f"[{i}/{total}] HTTP ERROR ({case_type}): {err_msg}")
            failures.append({"id": payload["id"], "case_type": case_type, "errors": [err_msg]})
        except Exception as e:
            print(f"[{i}/{total}] ERROR ({case_type}): {e}")
            failures.append({"id": payload["id"], "case_type": case_type, "errors": [str(e)]})

    score_pct = (fully_passed / total) * 100
    print("\n" + "=" * 50)
    print(f"ALL-KEYS EVALUATION SCORE: {fully_passed}/{total} ({score_pct:.1f}%)")
    print("=" * 50)

    if failures:
        print(f"\n{len(failures)} case(s) failed strict evaluation criteria.")
    else:
        print("\nAll 8 test cases satisfied 100% of schema constraints and target values.")


if __name__ == "__main__":
    run_evals()