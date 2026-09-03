import json
import logging
import time
from flask import Blueprint, request, jsonify

from data.dataset_store import dataset_store
from masking.masking_service import MaskingService
from actions.action_registry import action_registry
from ai.agent_service import agent_service

logger = logging.getLogger(__name__)

analyze_bp = Blueprint("analyze", __name__)


def _build_chart_data(action_name, result, masking):
    """Build chart-ready data from action results, using masked names."""
    mapping = masking.get_column_mapping()

    if action_name == "get_top_values" and "results" in result:
        chart = []
        for item in result["results"]:
            label = mapping.get(item.get("group", ""), item.get("group", ""))
            value = item.get("value", 0)
            chart.append({"name": label, "value": value})
        return {"type": "bar", "data": chart}

    if action_name == "get_bottom_values" and "results" in result:
        chart = []
        for item in result["results"]:
            label = mapping.get(item.get("group", ""), item.get("group", ""))
            value = item.get("value", 0)
            chart.append({"name": label, "value": value})
        return {"type": "bar", "data": chart}

    if action_name == "get_trend" and "results" in result:
        chart = []
        for item in result["results"]:
            chart.append({"date": item.get("date", ""), "value": item.get("value", 0)})
        return {"type": "line", "data": chart}

    if action_name == "get_missing_values":
        chart = [{
            "name": mapping.get(result.get("column", ""), result.get("column", "")),
            "missing": result.get("missing_count", 0),
            "present": result.get("total_rows", 0) - result.get("missing_count", 0),
        }]
        return {"type": "missing", "data": chart}

    if action_name in ("calculate_total", "calculate_average"):
        val_key = "total" if "total" in result else "average"
        chart = [{
            "name": mapping.get(result.get("column", ""), result.get("column", "")),
            "value": result.get(val_key, 0),
        }]
        return {"type": "metric", "data": chart}

    return None


def _mask_result_for_ai(action_name, result, masking):
    """Create a masked version of the result for the AI to explain."""
    mapping = masking.get_column_mapping()

    if action_name == "get_top_values" and "results" in result:
        masked_results = []
        for item in result["results"]:
            masked_item = {}
            for k, v in item.items():
                k_ph = mapping.get(k, k)
                if isinstance(v, (int, float)):
                    masked_item[k_ph] = masking.mask_value(v, "AMOUNT")
                elif isinstance(v, str):
                    masked_item[k_ph] = masking.mask_value(v, "ITEM")
                else:
                    masked_item[k_ph] = v
            masked_results.append(masked_item)
        return json.dumps({"results": masked_results})

    if action_name == "get_bottom_values" and "results" in result:
        masked_results = []
        for item in result["results"]:
            masked_item = {}
            for k, v in item.items():
                k_ph = mapping.get(k, k)
                if isinstance(v, (int, float)):
                    masked_item[k_ph] = masking.mask_value(v, "AMOUNT")
                elif isinstance(v, str):
                    masked_item[k_ph] = masking.mask_value(v, "ITEM")
                else:
                    masked_item[k_ph] = v
            masked_results.append(masked_item)
        return json.dumps({"results": masked_results})

    if action_name == "get_trend" and "results" in result:
        return json.dumps(result)

    if action_name == "get_missing_values":
        col_ph = mapping.get(result.get("column", ""), result.get("column", ""))
        return json.dumps({
            "column": col_ph,
            "missing_count": result["missing_count"],
            "total_rows": result["total_rows"],
            "missing_percentage": result["missing_percentage"],
        })

    if action_name in ("calculate_total", "calculate_average"):
        val_key = "total" if "total" in result else "average"
        col_ph = mapping.get(result.get("column", ""), result.get("column", ""))
        masked_val = masking.mask_value(result[val_key], "AMOUNT")
        return json.dumps({val_key: masked_val, "column": col_ph})

    return json.dumps(result)


@analyze_bp.route("/api/analyze", methods=["POST"])
def analyze():
    start_time = time.time()

    data = request.get_json()
    if not data or "dataset_id" not in data or "question" not in data:
        return jsonify({"error": "Missing dataset_id or question"}), 400

    dataset_id = data["dataset_id"]
    question = data["question"].strip()

    if not question:
        return jsonify({"error": "Question cannot be empty"}), 400

    record = dataset_store.get(dataset_id)
    if not record:
        return jsonify({"error": "Dataset not found. Please upload a CSV first."}), 404

    masking = getattr(record, "masking_service", None)
    if not masking:
        return jsonify({"error": "Dataset masking not initialized"}), 500

    try:
        # Build masked schema text for AI
        masked_schema = []
        for col in record.schema:
            masked_schema.append(f"{col['name']} = {col['type']}")
        schema_text = "\n".join(masked_schema)

        # Build actions text for AI
        actions_list = action_registry.list_actions()
        actions_text = ""
        for action in actions_list:
            actions_text += f"\n{action['name']}:\n"
            actions_text += f"  Description: {action['description']}\n"
            actions_text += f"  Parameters: {json.dumps(action['parameters'])}\n"

        # Step 1: AI selects action
        logger.info(f"Question: {question}")
        ai_response = agent_service.select_action(question, schema_text, actions_text)
        logger.info(f"AI response: {json.dumps(ai_response)}")

        action_name = ai_response.get("action", "unsupported")
        action_params = ai_response.get("parameters", {})

        if action_name == "unsupported":
            reason = ai_response.get("reason", "This question cannot be answered with available actions.")
            return jsonify({
                "answer": reason,
                "action": "unsupported",
                "success": True,
            })

        # Step 2: Validate the action exists
        action = action_registry.get(action_name)
        if not action:
            return jsonify({
                "answer": f"Invalid action selected: {action_name}",
                "action": action_name,
                "success": False,
            })

        # Step 3: Map masked column names to real column names
        real_params = {}
        for key, val in action_params.items():
            if isinstance(val, str) and val in masking.get_reverse_mapping():
                real_params[key] = masking.unmask_column(val)
            else:
                real_params[key] = val

        # Step 4: Validate and execute the action
        real_available = list(masking.get_reverse_mapping().keys())
        result = action_registry.validate_and_execute(
            action_name, real_params, real_available, record.df
        )

        # Step 5: Build chart data from raw result (for frontend visualization)
        chart_data = _build_chart_data(action_name, result, masking)

        # Step 6: Mask the result before sending to AI
        masked_result = _mask_result_for_ai(action_name, result, masking)

        # Step 7: AI explains the masked result
        explanation = agent_service.explain_result(question, masked_result)

        # Step 8: Unmask the explanation
        final_answer = masking.unmask_text(explanation)

        elapsed = time.time() - start_time
        logger.info(f"Analysis completed in {elapsed:.2f}s, action={action_name}")

        response = {
            "answer": final_answer,
            "action": action_name,
            "success": True,
        }
        if chart_data:
            response["chart"] = chart_data

        return jsonify(response)

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        return jsonify({
            "answer": f"Analysis error: {str(e)}",
            "action": action_name if 'action_name' in dir() else "unknown",
            "success": False,
            "error": str(e),
        }), 400
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        elapsed = time.time() - start_time
        logger.info(f"Analysis failed in {elapsed:.2f}s")
        return jsonify({
            "answer": "An error occurred while analyzing your data. Please try again.",
            "action": "error",
            "success": False,
            "error": str(e),
        }), 500
