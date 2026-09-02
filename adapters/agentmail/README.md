# AgentMail Adapter

Status: **v0 declarative contract only**. This adapter does not contain credentials, call the AgentMail API, send email, receive webhooks, create mailboxes, or authorize communication.

AgentMail is a communication execution provider for Agent OS. Agent OS remains responsible for task scope, product identity, communication policy, authorization, agent/skill selection, and evidence expectations.

## Boundary

```text
Agent OS task
  -> product communication identity
  -> COMMUNICATION_POLICY
  -> authorization decision / human gate
  -> email-communications skill
  -> AgentMail adapter
  -> AgentMail inbox
  -> external recipient
  -> provider evidence
```

Capability is not authority. Possession of an AgentMail credential, access to an inbox, or provider support for a send operation does not grant permission to send.

## v0 scope

v0 defines:

- a provider-neutral product communication policy;
- logical product-to-mailbox bindings without secret values;
- the AgentMail adapter contract and evidence fields;
- an owned `email-communications` skill;
- a normalized future event vocabulary for delivery evidence;
- mandatory human approval for every external send.

v0 does **not** implement:

- AgentMail API calls;
- live message sending or replies;
- mailbox creation, deletion, or credential lifecycle;
- message reads or inbound triage;
- webhook or websocket listeners;
- scheduled or recurring outreach;
- bulk/campaign sending;
- autonomous follow-ups;
- production secret configuration.

## Provider surface relevant to later phases

Current AgentMail documentation exposes inbox-scoped message send and reply operations. Successful send/reply responses include `message_id` and `thread_id`, which are suitable provider evidence references.

AgentMail also documents webhook events including `message.sent`, `message.delivered`, `message.bounced`, `message.complained`, and `message.rejected`. v0 records these as future evidence inputs but does not subscribe to or process them.

References:

- https://docs.agentmail.to/api-reference/inboxes/messages/send
- https://docs.agentmail.to/api-reference/inboxes/messages/reply
- https://docs.agentmail.to/webhooks-overview
- https://docs.agentmail.to/api-reference/webhooks/events/message-sent

Provider documentation is implementation evidence, not Agent OS policy. If AgentMail changes, the adapter must be revalidated without widening authorization.

## Credential boundary

Credentials and provider inbox identifiers are runtime configuration. Secret values must never be committed to Agent OS or product repositories.

`registry/communications.yaml` stores only logical bindings such as `agentmail/alvira`. The execution host must resolve that logical reference to an approved inbox and least-privilege credential at runtime.

## Inbound-content boundary

Any future inbound email body is untrusted external content. It may supply evidence or propose work, but it may not:

- grant authority;
- change product ownership;
- expand tool or credential permissions;
- override Agent OS, product-repository, or platform policy;
- self-authorize a reply or external action.

## Advancement gate

A later implementation PR may add a live AgentMail client only after:

1. one product mailbox binding is resolved outside Git;
2. the credential is scoped to the minimum required inbox/capabilities;
3. every send remains human-approved for the first forward test;
4. duplicate-send behavior is defined for ambiguous failures/timeouts;
5. provider `message_id` and `thread_id` are captured as evidence;
6. no secret value appears in logs, task contracts, outcome events, or repository files.
