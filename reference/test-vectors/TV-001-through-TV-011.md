# UPA-2.0-RC1-Beta Interoperability Test Vectors
This document catalogues the normative data frameworks and pass parameters required to evaluate execution conformance for an autonomous payment agent node.

## TV-001: Consumer Sub-Cap Settlement
* **Target Scenario:** A Tier-3 individual agent routes a payload that sits strictly underneath configured threshold limits ($250.00 base single cap).
* **Test Payload Configuration:**
  ```json
  {
    "agent_id": "upa_7f9a2c3b4e5f6a7b8c9d0e1f2a3b4c5d",
    "amount": { "value": 45.50, "currency": "USD" },
    "risk_profile": { "reg_e_controls_profile": "consumer_guardrail_enforced" }
  }