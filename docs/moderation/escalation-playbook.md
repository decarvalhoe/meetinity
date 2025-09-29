# Moderation Escalation Playbook

This playbook describes how the moderation-service, operations team and partner services collaborate when risky content is detected.

## 1. Automated filter response

1. The messaging or event services call `POST /v1/filters/check` before saving user-generated content.
2. If the filter result is `blocked`, the originating service rejects the payload and surfaces a user-friendly message.
3. For `needs_review`, the content is stored but marked for human review and a moderation case is opened automatically.
4. Every automated decision creates a Kafka event on `moderation.events`, which analytics and compliance teams monitor for anomalies.

## 2. Case triage

1. Auto-generated cases appear in the moderation dashboard with severity, automated score and contextual labels.
2. Duty moderators assign cases to themselves using `POST /v1/reports/<case_id>/assign`.
3. High severity signals (e.g. self-harm, threats) trigger immediate escalation to the Trust & Safety rotation by tagging the case with `escalated` status.
4. Redis-based counters enforce per-user rate limits; if an account exceeds quotas, the moderation-service flags it for identity verification.

## 3. Reviewer actions

1. Reviewers document their decisions with `POST /v1/reports/<case_id>/decision`.
2. The service publishes `case.resolved` events so notification-service can inform impacted users.
3. Sanctions (suspensions, bans) are executed in user-service via privileged APIs; the moderation record stores links to those actions.
4. Metrics: reviewers should close urgent cases within 30 minutes and standard cases within 8 working hours.

## 4. Appeals

1. Users submit appeals via the product UI, which proxies to `POST /v1/reports/<case_id>/appeals`.
2. Appeals are handled by a separate reviewer pool to maintain neutrality.
3. `POST /v1/reports/appeals/<appeal_id>/decision` records the final verdict and, if overturned, triggers content restoration in the originating service.
4. All appeal decisions are logged for quarterly policy audits.

## 5. Incident escalation

1. If multiple cases indicate a coordinated attack or policy gap, moderators use `POST /v1/admin/escalations` to bulk escalate cases to incident response.
2. The incident lead assembles a war-room including engineering, product, communications and legal stakeholders.
3. Kafka event streams are replayed to reconstruct timelines, and the scripts in `services/moderation-service/scripts/` can export case data for further analysis.
4. After containment, policy updates are proposed, and playbooks are amended to capture lessons learned.

## 6. Communication & audit

- Weekly summaries are exported to CSV (`export_cases.py`) and stored in the compliance data lake.
- Audit trails include automated filter outputs, reviewer notes, timestamps and actor identities.
- SOC 2 controls require demonstrating that escalations followed this playbook; deviations must be logged as exceptions.

Maintain this document alongside any policy changes to keep operations aligned.
