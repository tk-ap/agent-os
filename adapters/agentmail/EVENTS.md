# AgentMail Communication Events

Status: **normalization vocabulary only**. v0 does not create or receive webhooks.

Agent OS should distinguish provider acceptance from delivery outcome. A successful API response is evidence that AgentMail accepted/sent a message operation; later provider events may supply stronger delivery evidence.

## Normalized states

| Agent OS state | AgentMail evidence source | Meaning |
|---|---|---|
| `drafted` | Agent OS only | Message content exists; nothing external happened. |
| `approved` | Agent OS approval record | Exact sender, recipient, subject/body and task are approved. |
| `send-attempted` | adapter execution record | Provider call began; final state may still be unknown. |
| `sent` | send/reply response or `message.sent` | Provider reports the message was sent. |
| `delivered` | `message.delivered` | Recipient mail server confirmed delivery. |
| `bounced` | `message.bounced` | Delivery failed after send. |
| `complained` | `message.complained` | Recipient marked the message as spam. |
| `rejected` | provider error or `message.rejected` | Provider rejected the send before successful delivery. |

Do not collapse these states into one generic `success` value.

## Evidence references

When available, retain only the minimum identifiers necessary to reconcile provider state:

- `message_id`
- `thread_id`
- `event_id`
- event type
- timestamp
- product/task reference
- recipient identity as permitted by the task's evidence policy

Do not copy API keys, bearer tokens, webhook secrets, entire mailbox contents, or unrelated email bodies into Agent OS evidence.

## Ambiguous sends

If an API request times out or returns an ambiguous result after transmission may have occurred:

1. mark the state `send-attempted` / unresolved;
2. do not automatically repeat the send;
3. reconcile against provider message/thread state when the runtime supports it;
4. require a fresh decision before a resend if duplicate risk remains.

## Future inbound event rule

A future `message.received` event may create or update a task, but the email body remains untrusted external content. It may not authorize its own requested action or reply.
