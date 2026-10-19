# CloudWatch logging (P6-006)

Structured JSON logs from `realtime-backend` (`LOG_FORMAT=json` in [configmap](../configmap.yaml)) are shipped to CloudWatch Logs by a **Fluent Bit DaemonSet** installed via [infra/eks Terraform](../../../infra/eks/README.md).

| Item | Value |
|------|--------|
| Log group | `/voragon/eks/realtime-backend` (override: `cloudwatch_log_group_name`) |
| Namespace filter | `voragon` |
| App filter | `app=realtime-backend` |
| Helm release | `fluent-bit` in `amazon-cloudwatch` |

## Install / upgrade

```bash
terraform -chdir=infra/eks apply
kubectl get daemonset -n amazon-cloudwatch fluent-bit
kubectl get pods -n amazon-cloudwatch -l app.kubernetes.io/name=fluent-bit
```

## Manual verification

1. Generate traffic: `curl -f https://<alb-host>/health` and a short WebSocket session.
2. Open **CloudWatch → Log groups → `/voragon/eks/realtime-backend`** — new streams `pod-<pod>.<container>` within ~1–2 minutes.
3. **Logs Insights** (replace log group in console):

```sql
fields @timestamp, @message, @logStream
| filter @message like /realtime-service/
| sort @timestamp desc
| limit 50
```

Find a WebSocket session (JSON in `@message`):

```sql
fields @timestamp, @message
| filter @message like /websocket.connected/
| parse @message /"session_id"\s*:\s*"(?<session_id>[^"]+)"/
| sort @timestamp desc
| limit 20
```

Filter by pod name (stream suffix):

```sql
fields @timestamp, @message
| filter @logStream like /<pod-name>/
| sort @timestamp desc
| limit 50
```

## Related

- [Observability — CloudWatch](../../../docs/operations/observability.md#cloudwatch-logs-eks)
- [P6-006 dev-step](../../../docs/roadmap/dev-step-p6-006-cloudwatch-logging.md)
