# Routing foundation note

AgentOS is the routing authority. Interfaces such as Hermes Desktop, Terminal Velocity, Telegram, schedulers, or future workspace surfaces consume AgentOS routing decisions and do not own durable routing policy.

The router answers two questions independently:

1. Which durable agent identity owns this task?
2. Which replaceable harness/intelligence tier should execute the current step?

Persistence answers a different question: what work exists, what state is it in, what routing decisions were made, what attempts occurred, and what evidence was produced?

This separation is required to preserve autonomous continuation when a harness crashes, reaches quota, becomes unavailable, or is replaced.
