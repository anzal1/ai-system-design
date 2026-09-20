"""An agent tool-use loop from scratch.

Everything here is deterministic, stdlib only, and runs offline. The "model"
is a scripted decision table so that the interesting part, the control plane
around the model, is the whole program.

Run: python3 agent_loop.py
"""

import json
import time

# ---------------------------------------------------------------------------
# Tool registry with JSON-schema-style validation
# ---------------------------------------------------------------------------


class SchemaError(Exception):
    pass


def validate_schema(schema, args):
    """Validate args against a small JSON-schema subset.

    Supports: type object, properties, required, and property types
    string / integer / number / boolean. Rejects unknown properties, the
    same posture a strict tool gateway takes in production.
    """
    if schema.get("type") != "object":
        raise SchemaError("only object schemas are supported")
    if not isinstance(args, dict):
        raise SchemaError("arguments must be an object, got %r" % type(args).__name__)

    props = schema.get("properties", {})
    for key in schema.get("required", []):
        if key not in args:
            raise SchemaError("missing required argument: %s" % key)

    type_map = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
    }
    for key, value in args.items():
        if key not in props:
            raise SchemaError("unknown argument: %s" % key)
        expected = props[key]["type"]
        py = type_map[expected]
        if expected == "integer" and isinstance(value, bool):
            raise SchemaError("argument %s must be integer, got boolean" % key)
        if not isinstance(value, py):
            raise SchemaError(
                "argument %s must be %s, got %s" % (key, expected, type(value).__name__)
            )


class Tool:
    def __init__(self, name, description, schema, handler, cost, policy_class):
        self.name = name
        self.description = description
        self.schema = schema
        self.handler = handler
        self.cost = cost  # pretend dollars per call
        self.policy_class = policy_class  # "allow" | "confirm" | "deny"


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, tool):
        self._tools[tool.name] = tool

    def get(self, name):
        if name not in self._tools:
            raise KeyError("unknown tool: %s" % name)
        return self._tools[name]


# ---------------------------------------------------------------------------
# Policy gate, separate from the model on purpose
# ---------------------------------------------------------------------------


class PolicyGate:
    """Classifies tool calls as allow, confirm, or deny.

    The decision comes from the registry's policy class plus an approval
    callback for confirm-class calls. The model never gets a vote.
    """

    def __init__(self, approver):
        self.approver = approver  # callable(tool_name, args) -> bool

    def check(self, tool, args):
        if tool.policy_class == "deny":
            return ("deny", "tool %s is deny-class for this principal" % tool.name)
        if tool.policy_class == "confirm":
            if self.approver(tool.name, args):
                return ("allow", "confirm-class call approved")
            return ("deny", "confirm-class call rejected by approver")
        return ("allow", "allow-class tool")


# ---------------------------------------------------------------------------
# Budgets and loop detection
# ---------------------------------------------------------------------------


class Budget:
    def __init__(self, max_steps, max_cost):
        self.max_steps = max_steps
        self.max_cost = max_cost
        self.steps = 0
        self.cost = 0.0

    def charge(self, cost):
        self.steps += 1
        self.cost += cost

    def exceeded(self):
        if self.steps >= self.max_steps:
            return "step budget exhausted (%d steps)" % self.max_steps
        if self.cost >= self.max_cost:
            return "cost budget exhausted ($%.2f)" % self.cost
        return None


class LoopDetector:
    """Flags N identical consecutive tool calls.

    Identical means same tool name and same canonicalized arguments. A model
    that repeats a failing call is the single most common agent pathology,
    and it burns budget while producing nothing new.
    """

    def __init__(self, threshold=3):
        self.threshold = threshold
        self._last_key = None
        self._run_length = 0

    def observe(self, tool_name, args):
        key = tool_name + ":" + json.dumps(args, sort_keys=True)
        if key == self._last_key:
            self._run_length += 1
        else:
            self._last_key = key
            self._run_length = 1
        return self._run_length >= self.threshold


# ---------------------------------------------------------------------------
# The mock model: a scripted decision table
# ---------------------------------------------------------------------------


class ScriptedModel:
    """Maps (task, last observation) to the next action.

    Each task has an ordered list of rules. A rule is a predicate on the last
    observation plus the action to emit. First matching rule wins. This is
    obviously not a language model. That is the point: the loop cannot tell
    the difference, which shows how little of an agent's safety lives in
    the model itself.
    """

    def __init__(self, decision_tables):
        self.decision_tables = decision_tables

    def next_action(self, task, last_observation):
        for predicate, action in self.decision_tables[task]:
            if predicate(last_observation):
                return action
        return {"type": "final", "message": "no rule matched, giving up"}


# ---------------------------------------------------------------------------
# The agent loop itself
# ---------------------------------------------------------------------------


def run_agent(task, model, registry, gate, budget, loop_detector, trace):
    """Think, validate, gate, execute, observe. Repeat until a stop reason."""
    last_observation = None
    while True:
        over = budget.exceeded()
        if over:
            trace.append({"event": "stop", "reason": "budget", "detail": over})
            return {"stop_reason": "budget", "detail": over}

        action = model.next_action(task, last_observation)
        trace.append({"event": "proposal", "action": action})

        if action["type"] == "final":
            trace.append({"event": "stop", "reason": "final"})
            return {"stop_reason": "final", "message": action["message"]}

        name, args = action["tool"], action["args"]

        try:
            tool = registry.get(name)
            validate_schema(tool.schema, args)
        except (KeyError, SchemaError) as exc:
            trace.append({"event": "validation_error", "detail": str(exc)})
            last_observation = {"error": str(exc)}
            budget.charge(0.0)
            continue

        verdict, reason = gate.check(tool, args)
        trace.append({"event": "policy", "verdict": verdict, "reason": reason})
        if verdict == "deny":
            trace.append({"event": "stop", "reason": "policy_denied", "detail": reason})
            return {"stop_reason": "policy_denied", "detail": reason}

        if loop_detector.observe(name, args):
            detail = "identical call %s repeated %d times" % (name, loop_detector.threshold)
            trace.append({"event": "stop", "reason": "loop_detected", "detail": detail})
            return {"stop_reason": "loop_detected", "detail": detail}

        started = time.time()
        result = tool.handler(args)
        budget.charge(tool.cost)
        trace.append(
            {
                "event": "tool_result",
                "tool": name,
                "args": args,
                "result": result,
                "cost": tool.cost,
                "latency_ms": round((time.time() - started) * 1000, 2),
            }
        )
        last_observation = result


# ---------------------------------------------------------------------------
# Demo world: a tiny order-support backend
# ---------------------------------------------------------------------------

ORDERS = {
    1042: {"item": "usb-c dock", "amount": 89.0, "status": "delivered", "days_ago": 9},
}

REFUND_POLICY = {"window_days": 30, "max_auto_amount": 100.0}


def build_registry():
    registry = ToolRegistry()
    registry.register(
        Tool(
            name="get_order",
            description="Look up an order by id. Read only.",
            schema={
                "type": "object",
                "properties": {"order_id": {"type": "integer"}},
                "required": ["order_id"],
            },
            handler=lambda a: ORDERS.get(a["order_id"], {"error": "not found"}),
            cost=0.01,
            policy_class="allow",
        )
    )
    registry.register(
        Tool(
            name="get_refund_policy",
            description="Fetch the current refund policy. Read only.",
            schema={"type": "object", "properties": {}, "required": []},
            handler=lambda a: REFUND_POLICY,
            cost=0.01,
            policy_class="allow",
        )
    )
    registry.register(
        Tool(
            name="issue_refund",
            description="Issue a refund. Write with financial side effect.",
            schema={
                "type": "object",
                "properties": {
                    "order_id": {"type": "integer"},
                    "amount": {"type": "number"},
                },
                "required": ["order_id", "amount"],
            },
            handler=lambda a: {"refunded": a["amount"], "order_id": a["order_id"]},
            cost=0.02,
            policy_class="confirm",
        )
    )
    registry.register(
        Tool(
            name="delete_customer_record",
            description="Hard-delete a customer record. Irreversible.",
            schema={
                "type": "object",
                "properties": {"customer_id": {"type": "integer"}},
                "required": ["customer_id"],
            },
            handler=lambda a: {"deleted": a["customer_id"]},
            cost=0.02,
            policy_class="deny",
        )
    )
    registry.register(
        Tool(
            name="search_kb",
            description="Search the knowledge base. Read only.",
            schema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            handler=lambda a: {"hits": []},  # always empty, to bait a retry loop
            cost=0.01,
            policy_class="allow",
        )
    )
    return registry


def build_model():
    def obs_has(key):
        return lambda obs: isinstance(obs, dict) and key in obs

    def always(obs):
        return True

    def is_start(obs):
        return obs is None

    tables = {
        # Task 1: multi-step refund. Look up the order, fetch policy, refund.
        "refund order 1042": [
            (is_start, {"type": "tool_call", "tool": "get_order", "args": {"order_id": 1042}}),
            (obs_has("status"), {"type": "tool_call", "tool": "get_refund_policy", "args": {}}),
            (
                obs_has("window_days"),
                {
                    "type": "tool_call",
                    "tool": "issue_refund",
                    "args": {"order_id": 1042, "amount": 89.0},
                },
            ),
            (
                obs_has("refunded"),
                {"type": "final", "message": "Refunded $89.00 for order 1042."},
            ),
        ],
        # Task 2: the "model" decides deletion is the fix. Policy says no.
        "close account for customer 7": [
            (
                is_start,
                {
                    "type": "tool_call",
                    "tool": "delete_customer_record",
                    "args": {"customer_id": 7},
                },
            ),
        ],
        # Task 3: search returns nothing, the model retries the same call forever.
        "find docs about quantum billing": [
            (
                always,
                {
                    "type": "tool_call",
                    "tool": "search_kb",
                    "args": {"query": "quantum billing"},
                },
            ),
        ],
    }
    return ScriptedModel(tables)


def print_trace(trace):
    for entry in trace:
        line = dict(entry)
        event = line.pop("event")
        print("  [%-16s] %s" % (event, json.dumps(line, sort_keys=True)))


def run_demo():
    model = build_model()
    registry = build_registry()

    def approver(tool_name, args):
        # Scripted stand-in for a human or deterministic rule engine.
        # Refunds within policy get approved automatically.
        if tool_name == "issue_refund":
            return args["amount"] <= REFUND_POLICY["max_auto_amount"]
        return False

    gate = PolicyGate(approver)

    print("=" * 72)
    print("RUN 1: multi-step task that succeeds")
    print("=" * 72)
    trace1 = []
    r1 = run_agent(
        "refund order 1042",
        model,
        registry,
        gate,
        Budget(max_steps=8, max_cost=1.0),
        LoopDetector(threshold=3),
        trace1,
    )
    print_trace(trace1)
    print("  result: %s" % json.dumps(r1))
    assert r1["stop_reason"] == "final", r1
    assert "89.00" in r1["message"]
    tools_used = [e["tool"] for e in trace1 if e["event"] == "tool_result"]
    assert tools_used == ["get_order", "get_refund_policy", "issue_refund"], tools_used

    print()
    print("=" * 72)
    print("RUN 2: task stopped by the policy gate")
    print("=" * 72)
    trace2 = []
    r2 = run_agent(
        "close account for customer 7",
        model,
        registry,
        gate,
        Budget(max_steps=8, max_cost=1.0),
        LoopDetector(threshold=3),
        trace2,
    )
    print_trace(trace2)
    print("  result: %s" % json.dumps(r2))
    assert r2["stop_reason"] == "policy_denied", r2
    executed = [e for e in trace2 if e["event"] == "tool_result"]
    assert executed == [], "deny-class tool must never execute"

    print()
    print("=" * 72)
    print("RUN 3: runaway loop caught by loop detection")
    print("=" * 72)
    trace3 = []
    r3 = run_agent(
        "find docs about quantum billing",
        model,
        registry,
        gate,
        Budget(max_steps=20, max_cost=1.0),
        LoopDetector(threshold=3),
        trace3,
    )
    print_trace(trace3)
    print("  result: %s" % json.dumps(r3))
    assert r3["stop_reason"] == "loop_detected", r3
    executed = [e for e in trace3 if e["event"] == "tool_result"]
    # Threshold 3 means the third identical proposal is stopped before it runs.
    assert len(executed) == 2, executed
    assert len(executed) < 20, "loop detector must fire well before the step budget"

    print()
    print("All assertions passed.")
    print(
        "Takeaway: three different stop reasons, and the model never produced any "
        "of them. The control plane did."
    )


if __name__ == "__main__":
    run_demo()
