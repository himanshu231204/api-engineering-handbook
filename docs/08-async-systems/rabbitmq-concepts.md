# RabbitMQ Concepts

> [!TIP]
> **In one line:** RabbitMQ routes messages from producers through exchanges, via bindings, into queues, where consumers take and acknowledge them; the routing rules, not the queues, are its distinctive idea.
>
> **In plain English:** Instead of dropping letters straight into one mailbox, you hand them to a sorting office that reads the address label and copies or forwards each letter to the right mailboxes. You then decide how each mailbox is emptied, how many letters a person may carry at once, and where undeliverable letters go.
>
> **You'll be able to:** choose between direct, topic and fanout exchanges · configure acks, prefetch, durability and dead-lettering · explain what RabbitMQ does and does not guarantee

## Why This Matters

[Message Queues](message-queues.md) described the general idea; [Workers](workers.md) described the consuming side. RabbitMQ is the most widely deployed implementation of the classic **broker** model, speaking AMQP 0-9-1 (plus other protocols through plugins), and it is a common backend for Celery, many microservice platforms and enterprise integration. Knowing its vocabulary pays off even if you end up on a different broker, because SQS, Azure Service Bus and Google Pub/Sub use closely related ideas.

What makes RabbitMQ different from "a list in Redis" is *routing*. One published event can go to the billing queue, the audit queue and a search-index queue without the producer knowing any of them exist. And it makes a handful of reliability features (acks, durability, dead-lettering, prefetch) explicit settings you must understand, because the defaults in client libraries are often not the production-safe choice.

## Core Concept

RabbitMQ has five core objects.

- **Producer** publishes a message to an **exchange**, along with a **routing key** (a string label such as `order.eu.created`). Producers do not publish to queues directly.
- **Exchange** is a routing engine with no storage. It receives a message and decides which queues get a copy, according to its **type** and the **bindings** attached to it.
- **Binding** links an exchange to a queue, optionally with a **binding key** or pattern: "send messages matching this to that queue."
- **Queue** is the buffer. It stores messages in order until a consumer takes them. Queues are where durability, length limits, TTLs and dead-lettering are configured.
- **Consumer** subscribes to a queue, receives messages, and **acks** them.

The exchange types:

- **direct**: delivers to queues whose binding key equals the routing key exactly. Good for "send job type X to the X workers."
- **topic**: routing keys are dot-separated words, and bindings use patterns where `*` matches exactly one word and `#` matches zero or more. `order.eu.*` matches `order.eu.created`; `order.#` matches every key beginning `order.`. This is the workhorse for event routing.
- **fanout**: ignores the key and copies to every bound queue. Broadcasts such as cache invalidation.
- **headers**: matches on message headers rather than the key; rarely needed.
- **default exchange**: an unnamed direct exchange where every queue is automatically bound under its own name, so publishing with routing key `pdf_queue` goes to `pdf_queue`. It is why beginner tutorials appear to "send to a queue."

Two facts are worth stating precisely. First, **a message copied to N queues is N independent messages**: each queue's consumers ack their own copy. Competing consumers on *one* queue share work; separate queues each get everything. Second, a message with no matching binding is **silently discarded** unless the publisher sets the `mandatory` flag (and handles returns) or the exchange has an alternate exchange configured.

## Mental Model

A sorting office. Senders do not know which mailbox belongs to whom; they write a label (routing key) and hand the item over the counter (exchange). The sorting rules (bindings) say "labels starting with `order.eu` go to the Europe tray, anything starting with `order` also gets a copy in the audit tray." Each tray (queue) holds items until a clerk (consumer) signs for them (ack). Direct, topic and fanout are three sorting policies: exact match, pattern match, and "photocopy for everyone."

## How It Works

**Publishing.** The producer opens a connection and a channel (a lightweight multiplexed session; use one channel per thread or task), publishes with a routing key, and, for anything that matters, enables **publisher confirms**. A confirm is the broker saying "I have taken responsibility for this message" (for a persistent message on a durable queue, after it has been written to disk, and for quorum queues after a majority of replicas have it). Without confirms, a publish can be lost between your socket and the broker's disk with no error.

**Durability needs three things.** For a message to survive a broker restart you need: a **durable exchange**, a **durable queue**, and a **persistent message** (`delivery_mode = 2`). Miss one and the message or the topology vanishes on restart. Persistence plus confirms is "reasonably safe"; it is not magic. Replication is what protects you from losing a node: use **quorum queues**, which replicate through Raft and tolerate minority node failure, rather than classic single-node queues for important data.

**Consuming and acks.** Consumers receive messages by push (`basic.consume`) and must acknowledge. The three outcomes are `ack` (done, delete it), `nack`/`reject` with `requeue=true` (put it back), and `nack`/`reject` with `requeue=false` (discard it, or dead-letter it if the queue has a DLX). If the consumer's channel or connection closes with messages unacked, the broker requeues them, marked `redelivered`. This gives **at-least-once** delivery when you ack after processing. If you use `auto_ack`, the broker considers the message done as soon as it is sent, which is at-most-once: a crash loses it. Use manual acks.

**Prefetch (QoS).** `basic.qos(prefetch_count=N)` caps the number of unacknowledged messages the broker will push to a consumer. Without it, a consumer can be sent the entire queue at once, hoarding messages that other workers could have processed and exploding its own memory. A small prefetch gives fair distribution and natural backpressure; a larger one improves throughput when jobs are short. Starting values in the range of 1 to 20 are typical; tune against job duration. This is the direct equivalent of the concurrency limit in [Workers](workers.md).

**Dead-letter exchanges (DLX).** A queue can name a DLX in its arguments. A message is dead-lettered when it is rejected without requeue, when its TTL expires, when the queue exceeds its length limit, or, on quorum queues, when it exceeds the configured `x-delivery-limit` (the poison-message guard). The DLX is an ordinary exchange, so dead messages route to a normal queue you can inspect, alert on and replay. Combined with a per-queue TTL, a "wait queue" with a DLX back to the main exchange is the standard way to implement delayed retry without a plugin.

**Ordering.** A single queue delivers in FIFO order to its consumers, but with several consumers, or after a requeue, completion order is not guaranteed. Requeued messages return to their original position where possible but redelivery can still interleave. If you need strict per-key ordering, use a single consumer on that queue or a partitioned design (RabbitMQ's consistent-hash exchange, or a log-based system, see [Kafka Concepts](kafka-concepts.md)).

**What RabbitMQ is not.** A classic queue is a *consume-and-delete* structure: once acked, a message is gone. There is no replaying history for a new consumer. (RabbitMQ Streams, a separate queue type, adds an append-only log with replay; that is a different tool inside the same broker.)

## Architecture

```mermaid
flowchart LR
    P["Producer"] -->|"key: order.eu.created"| X{{"orders\ntopic exchange"}}
    X -->|"order.eu.*"| Q1[("eu_orders")]
    X -->|"order.#"| Q2[("audit_log")]
    Q1 --> C1["Worker A\nprefetch 10"]
    Q1 --> C2["Worker B\nprefetch 10"]
    Q2 --> C3["Audit consumer"]
    Q1 -.->|"rejected or delivery limit"| DLX{{"orders.dlx"}}
    DLX --> DQ[("orders.dead")]
```

![RabbitMQ producer publishing a routing key to direct, topic and fanout exchanges, which copy the message to bound queues that consumers acknowledge](../assets/diagrams/08-rabbitmq-exchanges.svg)

Note that `eu_orders` is consumed by two competing workers (each message goes to one of them), while `audit_log` is a separate queue that independently receives its own copy of every matching message.

## Request / Response Example

AMQP itself is a binary protocol, but RabbitMQ's management plugin exposes an HTTP API that is ideal for inspection and debugging. (Publishing through it is for testing only; real producers use AMQP.)

```http
POST /api/exchanges/%2F/orders/publish HTTP/1.1
Host: rabbit.internal:15672
Authorization: Basic <base64 user:password from your secret store>
Content-Type: application/json

{
  "routing_key": "order.eu.created",
  "payload": "{\"order_id\": 501, \"total\": 4200}",
  "payload_encoding": "string",
  "properties": {"delivery_mode": 2, "content_type": "application/json"}
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"routed": true}
```

`routed: true` means at least one queue matched. It does *not* mean anyone processed the message. Inspecting a queue shows the health picture an operator needs:

```http
GET /api/queues/%2F/eu_orders HTTP/1.1

HTTP/1.1 200 OK
Content-Type: application/json

{"name": "eu_orders", "type": "quorum", "durable": true,
 "messages_ready": 1243, "messages_unacknowledged": 20, "consumers": 2,
 "arguments": {"x-dead-letter-exchange": "orders.dlx", "x-delivery-limit": 5}}
```

`messages_ready` growing while `consumers` stays flat is the signal to scale workers; `messages_unacknowledged` stuck high with few completions points at slow or hung consumers.

## Code Example

An `aio-pika` setup with a durable topic exchange, a quorum queue with a dead-letter exchange and delivery limit, publisher confirms, persistent messages, manual acks and a prefetch limit.

```python
# rabbit.py: pip install aio-pika
import asyncio
import json
import os

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message

AMQP_URL = os.environ["AMQP_URL"]  # e.g. amqps://user:pass@host/vhost, from the environment


async def declare_topology(channel: aio_pika.abc.AbstractChannel):
    # Dead-letter side first: a plain durable fanout exchange and a queue to hold dead messages.
    dlx = await channel.declare_exchange("orders.dlx", ExchangeType.FANOUT, durable=True)
    dead = await channel.declare_queue("orders.dead", durable=True)
    await dead.bind(dlx)

    orders = await channel.declare_exchange("orders", ExchangeType.TOPIC, durable=True)
    eu = await channel.declare_queue(
        "eu_orders",
        durable=True,
        arguments={
            "x-queue-type": "quorum",             # replicated, Raft-based
            "x-dead-letter-exchange": "orders.dlx",
            "x-delivery-limit": 5,                # poison guard: dead-letter after 5 deliveries
        },
    )
    await eu.bind(orders, routing_key="order.eu.*")
    return orders, eu


async def publish(orders: aio_pika.abc.AbstractExchange, order_id: int) -> None:
    body = json.dumps({"order_id": order_id}).encode()
    # aio-pika channels use publisher confirms by default, so this await returns
    # only after the broker accepts responsibility for the message.
    await orders.publish(
        Message(
            body,
            delivery_mode=DeliveryMode.PERSISTENT,   # survive a broker restart
            content_type="application/json",
            message_id=f"order-created-{order_id}",   # stable id for consumer-side dedup
        ),
        routing_key="order.eu.created",
        mandatory=True,   # raise if the message matches no queue instead of dropping it
    )


async def handle(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    try:
        data = json.loads(message.body)
        await process_order(data["order_id"], message.message_id)  # must be idempotent
    except (ValueError, KeyError):
        # Malformed: retrying cannot help. requeue=False dead-letters it immediately.
        await message.reject(requeue=False)
    except Exception:
        # Transient failure: requeue. The delivery limit dead-letters it eventually.
        await message.nack(requeue=True)
    else:
        await message.ack()          # ack only after the work succeeded


async def main():
    connection = await aio_pika.connect_robust(AMQP_URL)   # reconnects automatically
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)           # at most 10 unacked per consumer
        orders, eu = await declare_topology(channel)
        await publish(orders, 501)
        await eu.consume(handle)                            # manual ack mode by default
        await asyncio.Future()                              # run until cancelled


async def process_order(order_id: int, message_id: str | None) -> None:
    ...  # e.g. INSERT ... ON CONFLICT DO NOTHING keyed on message_id


if __name__ == "__main__":
    asyncio.run(main())
```

Limits to keep in mind: `mandatory` publishes raise on unroutable messages only when confirms are on and the broker returns them, so handle that exception in real code. `nack(requeue=True)` on a transient failure causes an immediate redelivery loop with no backoff; to get delay, route failures to a TTL "wait queue" whose DLX points back at the main exchange. Declarations are idempotent only if the arguments match the existing queue exactly; changing arguments on an existing queue fails with a `PRECONDITION_FAILED` error, so migrate by creating a new queue.

## Production Considerations

- **Use quorum queues** for data you cannot lose; classic mirrored queues are deprecated and removed in current RabbitMQ major versions. Quorum queues cost more disk and some throughput, so avoid them for disposable high-volume traffic.
- **Set a delivery limit and a DLX** on every work queue so a poison message cannot loop, and monitor the dead-letter queue.
- **Control memory and disk alarms.** When RabbitMQ hits its memory or disk watermarks it blocks publishers; a growing, unconsumed queue can cause exactly that. Use `x-max-length` or TTLs where dropping or dead-lettering is acceptable.
- **Prefer many small queues over one giant one**, but not millions of them: each queue has overhead.
- **Connection and channel hygiene.** Few long-lived connections, one channel per concurrent task, and automatic reconnection with topology re-declaration after failure.
- **Idempotent consumers.** A consumer can lose its connection after processing but before the ack, so the message will be redelivered. Assign stable `message_id`s and dedupe in the consumer. This is the same at-least-once requirement as everywhere in this part.
- **Security.** TLS on the wire, per-service credentials, per-vhost permissions limiting who can publish and consume. Credentials come from the environment or a secret manager.
- **Observe** queue depth (`ready` and `unacked`), consumer count, publish and ack rates, redelivery rate, and dead-letter queue growth.

## Common Mistakes

- **Publishing to a queue name** and not realizing the default exchange is doing the routing, then being confused when topologies change.
- **Auto-ack on important work**, which silently loses messages on a consumer crash.
- **No prefetch limit**, so one consumer hoards the backlog while others sit idle.
- **Durable queue but transient messages**, or the reverse, believing the data is safe.
- **No publisher confirms**, then discovering messages vanished during a broker restart or network blip.
- **Unbound exchange** or typo in a routing key; the message is silently dropped.
- **Requeue loops**: `nack(requeue=True)` for a permanently bad message, with no delivery limit.
- **Assuming exactly-once.** RabbitMQ gives at-most-once or at-least-once depending on acks. Effectively-once is achieved by idempotent consumers, not by the broker.
- **Using it as a log.** Classic queues delete on ack; if you want replay and many independent readers of history, evaluate streams or [Kafka](kafka-concepts.md).

## Best Practices

- Choose the exchange type by the shape of the traffic: direct for task types, topic for events, fanout for broadcast.
- Turn on publisher confirms, persistent messages, durable exchanges and queues, and manual acks for anything you care about.
- Set `prefetch_count` deliberately, and a delivery limit plus DLX on each work queue.
- Give each message a stable ID and make handlers idempotent.
- Declare topology in code at startup, with arguments that never change in place.
- Alert on queue age and growth, not only on broker liveness.

## AI Engineering Perspective

RabbitMQ is a good fit for the "fan-out then fan-in" shapes common in LLM systems. A document-ingestion event can be published once to a topic exchange and consumed by separate queues for chunking, embedding and metadata extraction, each scaled and rate-limited independently, which matches the pipeline stages in [RAG APIs](../16-rag-apis/README.md). Prefetch is a natural concurrency governor for model calls: set `prefetch_count` to the number of in-flight completions you can afford under your provider's rate limit, and the broker's flow control becomes your backpressure. Because LLM calls are slow and expensive, consumers should ack only after storing the result, and use the delivery limit to stop a prompt that deterministically crashes your parser from being retried indefinitely. For agent systems that dispatch tool calls to remote workers, work queues with a DLX give a clean way to capture failed tool invocations for inspection, a pattern revisited in [AI agents and MCP](../17-ai-agents-and-mcp/README.md).

## Exercises

**Beginner**
1. For a topic exchange with bindings `order.*.created` and `order.#`, state which bindings match the keys `order.eu.created`, `order.created` and `order.eu.shipped.late`.
2. Explain the difference between two consumers on one queue and two queues each with one consumer, in terms of who receives a given message.

**Intermediate**
1. Design the topology for delayed retry: a main queue, a 30-second wait queue with a DLX back to the main exchange, and a final dead-letter queue after three attempts. What header would you inspect to count attempts?
2. A queue shows `messages_unacknowledged = 500` and `consumers = 2` with prefetch 250. Explain what is happening and what you would change.

**Advanced**
1. Describe every point in the publish, store and consume path where a message can be lost or duplicated, and which setting (confirms, persistence, quorum queues, manual acks, idempotency) closes each gap. State what remains possible after all are applied.
2. You need strict per-customer ordering with 20 workers. Compare a consistent-hash exchange with one queue per shard to a log-based design, including what happens when a worker crashes mid-message.

## Key Takeaways

- Producers publish to **exchanges**; **bindings** route copies into **queues**; consumers **ack** from queues. Direct is exact match, topic is pattern match, fanout is broadcast.
- For safety combine durable exchange and queue, persistent messages, publisher confirms, manual acks, and quorum queues for replication; with those you get at-least-once, never exactly-once.
- Set `prefetch` for fairness and backpressure, and a delivery limit plus dead-letter exchange to contain poison messages.
- Classic queues delete on ack and do not support replay; use a log-based system when you need history.

### Check Yourself

<details markdown="1">
<summary>1. What is the role of an exchange, and why can't a producer publish straight to a queue?</summary>

An exchange applies routing rules (type plus bindings) to decide which queues receive a copy, which decouples producers from consumers. Publishing "to a queue" really goes through the default exchange, which routes by queue name.

</details>

<details markdown="1">
<summary>2. Why is a durable queue not enough to keep a message safe across a broker restart?</summary>

The message itself must be persistent and the exchange durable, and the publisher needs confirms to know the broker actually wrote it. A transient message in a durable queue is lost on restart, and an unconfirmed publish can be lost before it arrives.

</details>

<details markdown="1">
<summary>3. A malformed message makes your consumer throw, you call nack with requeue=true, and the queue's CPU spikes. What happened and how do you stop it?</summary>

The message is redelivered instantly in a tight loop because it can never succeed. Reject it with `requeue=false` when the error is permanent, and set a delivery limit plus dead-letter exchange so repeated failures get parked for inspection.

</details>

---
Back to the [Part 8 README](README.md).
