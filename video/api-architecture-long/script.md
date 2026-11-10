# Script — API Architecture at a Glance (long)

Runtime 08:27. Chapters:

- 00:00 Intro: API architecture at a glance
- 00:27 The big map
- 01:26 Who does what
- 03:23 Three requests
- 05:11 See it run
- 06:03 Don't over-build
- 07:27 Recap, quiz and what's next


## Intro

- **00:00** Your API request crosses five layers before it returns.
- **00:04** Add the wrong one, and you'll lose weeks debugging it.
- **00:07** Which layers does your API need? By the end of this video, you'll name each layer, trace three requests through them, and know when to skip one.
- **00:16** Here's the plan, in five parts.
- **00:18** One, the big map. Two, who does what. Three, three requests traced through it.
- **00:23** Four, a real run. And five, when not to add a layer.

## The big map

- **00:29** Picture an airport. Check in, security, then the gate. One job each, before you board.
- **00:35** A request travels the same way. A CDN may answer straight away. A gateway checks who you are. The app does the real work.
- **00:44** Here is the whole map, straight from the handbook. It starts with a client: a browser, a mobile app, another service, even an AI agent.
- **00:53** The client reaches a CDN or load balancer, then an API gateway, then your application service.
- **01:00** And behind the application sit four things: a cache, a database, a message queue with workers, and an AI gateway that reaches the language model providers.
- **01:12** The chapter draws the same system a second way, grouped into layers.
- **01:16** Edge. Gateway. Application. Data. And AI.
- **01:19** Five layers, each with a narrow job. Client, edge, gateway, application, then data and AI.

## Who does what

- **01:28** The handbook's mental model is a company org chart, not one person doing everything.
- **01:34** The CDN is the receptionist. If they already have your answer, they hand it over right there.
- **01:40** The gateway is security and routing. It checks your badge, then sends you to the right department.
- **01:46** The application service is that department, doing the real work. The database is the filing cabinet.
- **01:53** The queue is the ticket system. The AI gateway talks to outside AI vendors.
- **01:59** Zoom in on the gateway: one front door, one address for web, mobile and partner clients.
- **02:05** It does the shared chores once: authenticate, rate limit, and route to the right private service.
- **02:11** Fail a check, and the request is rejected right there: a 401, or a 429. No service does any work.
- **02:20** And it stays dumb. A gateway that also holds business logic stops being a gateway.
- **02:26** The cache sits beside the app. Reads check it first.
- **02:29** A hit comes back in about 1 millisecond. A miss reads the database, then saves the answer for next time.
- **02:36** On a write, the app updates the database and deletes the cached copy, so nobody reads stale data.
- **02:43** The queue is for work that shouldn't make the client wait. Like sending a confirmation email.
- **02:49** The API validates the request, drops a job on the queue, and answers right away.
- **02:55** Workers do the slow part later. If a worker crashes, the job goes back on the queue.
- **03:00** That buys you decoupling, durability, and a steady pace when traffic spikes.
- **03:06** The AI gateway is one front door for every model call. Your apps never talk to a provider directly.
- **03:13** It handles authentication, rate limits, caching, routing and cost tracking once, for everyone. And if a provider is down, it falls back to another.

## Three requests

- **03:25** Request one, a simple read: GET /products/9. It hits the CDN first.
- **03:31** If the CDN has the answer cached, it returns right there. Nothing behind it ever hears about the request.
- **03:39** If not, the gateway authenticates and rate limits, then routes it to the application service.
- **03:45** The app checks its cache. A hit skips the database. A miss queries it, then stores the result.
- **03:51** Then the response retraces the same path, back to the client.
- **03:55** Request two, a write: POST /orders. This is the handbook's end to end view of it.
- **04:01** A POST isn't cached, so it passes straight through to the application service.
- **04:06** The order service validates the body, commits to PostgreSQL in one transaction, updates Redis, and publishes a message to the queue.
- **04:15** A 201 comes back in roughly 20 to 150 milliseconds. The worker sends the email after the response, so the client never waits.
- **04:26** Request three, an AI chat message. The handbook traces it in seven steps.
- **04:31** The gateway validates the token and checks the rate limit. The app loads the conversation from PostgreSQL, and checks Redis.
- **04:40** Then the app calls the AI gateway, which routes to an available provider, with a fallback if the primary is down.
- **04:48** The answer streams back token by token, through the app and the gateway to the client.
- **04:53** And logging and cost tracking happen afterwards, through a queue, so they never slow the reply.
- **05:00** Same map, three different paths. A read can stop at the CDN. A write goes to the database and queues the slow work. A chat goes through the AI gateway.

## See it run

- **05:13** Now let's watch the AI layer for real. This is the handbook's LLM gateway example, a small FastAPI app.
- **05:21** Its setup is a few lines: providers in priority order, and a token bucket that allows five requests, refilling one per second.
- **05:31** Over the limit, the gateway answers 429. And every response gets a cost attached.
- **05:37** Five calls to the same chat endpoint. Four were served by the first provider.
- **05:42** On the fifth, it failed, and the gateway fell back to provider A, the only one that costs anything.
- **05:49** The usage endpoint rolls up cost per tenant: five requests, a fraction of a cent.
- **05:55** Now a burst of eight requests. The first five pass. The next three get a 429: rate limited, right at the gateway.

## Don't over-build

- **06:05** Now the most important rule. Not every API needs every layer. A small internal tool can be one application service with a database behind it, and that's the right architecture at that scale.
- **06:19** Each layer buys you something. A cache buys latency. A gateway buys central auth. A queue buys resilience. But the price is more moving parts, more failure modes, more to operate.
- **06:32** Mistake one. Assuming every API needs a gateway, a queue, and a cache from day one. Most don't, at first. Add a layer for a real problem, not a hypothetical one.
- **06:44** Mistake two. Treating microservices as automatically more production grade than a well built monolith. It depends on the problem. Part 11 covers it.
- **06:55** Mistake three. Bolting the AI layer on as an afterthought. It needs its own timeouts, fallbacks, and cost tracking.
- **07:03** A database query is usually fast and predictable. A model call can be slow, non-deterministic, and billed by usage. That's why it deserves its own box.
- **07:14** So Parts 14 to 17 add LLM gateways, token rate limits, prompt caching, and semantic caching. Ideas a typical CRUD API never needed.

## Recap

- **07:29** Let's recap.
- **07:30** A production API is a layered system: client, edge, gateway, application, then data and AI.
- **07:38** Each layer has one narrow job, and requests take different paths through them.
- **07:43** Add a layer only for a real problem, and treat the AI layer like the database.
- **07:48** And bookmark Part 18. It's the full production version of this map.
- **07:53** Quick check before you go. A POST /orders request must also send a confirmation email. How do you avoid making the client wait for it?
- **08:02** Pause and answer. Got it? Put the email on a queue as a background job. A worker sends it after the response.
- **08:10** Next up: the handbook's learning roadmap, a guided path through all 20 parts.
- **08:16** Or try the chapter's exercise: the layers a GET /orders/{id} request passes through, in a food delivery app.
- **08:24** Subscribe, and I'll see you in the next one.
