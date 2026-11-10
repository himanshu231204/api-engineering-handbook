# (beat, key, chapter, say, cap)   cap: [brackets] = highlighted keywords
# Source of truth: docs/00-introduction/api-architecture.md (+ the concept SVGs, diagrams/api-request-flow.md and examples/llm-gateway it points to).
CHAPTERS = {
  0: "Intro",
  1: "The big map",
  2: "Who does what",
  3: "Three requests",
  4: "See it run",
  5: "Don't over-build",
  6: "Recap",
}
B = []
def L(beat, key, ch, say, cap): B.append(dict(beat=beat, key=key, ch=ch, say=say, cap=cap))

# ---------------- intro ----------------
L("hook","h1",0,"Your API request crosses five layers before it returns.","Your API request crosses [five layers] before it returns.")
L("hook","h2",0,"Add the wrong one, and you'll lose weeks debugging it.","Add the [wrong] one, and you'll lose [weeks] debugging it.")
L("hook","h3",0,"Which layers does your API need? By the end of this video, you'll name each layer, trace three requests through them, and know when to skip one.","Which layers does [your API] need? Name them, [trace] three requests, know when to [skip].")

L("road","r1",0,"Here's the plan, in five parts.","Here's the plan, in [five] parts.")
L("road","r2",0,"One, the big map. Two, who does what. Three, three requests traced through it.","[Big map]. [Who does what]. [Three requests].")
L("road","r3",0,"Four, a real run. And five, when not to add a layer.","[A real run]. And when [not] to add a layer.")

# ---------------- 1 the big map ----------------
L("air","a1",1,"Picture an airport. Check in, security, then the gate. One job each, before you board.","An airport: [check-in], [security], the [gate]. One [job] each.")
L("air","a2",1,"A request travels the same way. A C D N may answer straight away. A gateway checks who you are. The app does the real work.","A [CDN] may answer. A [gateway] checks who you are. The [app] does the work.")

L("map","m1",1,"Here is the whole map, straight from the handbook. It starts with a client: a browser, a mobile app, another service, even an AI agent.","The whole [map]. It starts with a [client]: browser, app, service, [AI agent].")
L("map","m2",1,"The client reaches a C D N or load balancer, then an API gateway, then your application service.","[CDN], then [gateway], then your [application] service.")
L("map","m3",1,"And behind the application sit four things: a cache, a database, a message queue with workers, and an AI gateway that reaches the language model providers.","Behind the app: [cache], [database], [queue], [AI gateway].")

L("lay","l1",1,"The chapter draws the same system a second way, grouped into layers.","The same system, grouped into [layers].")
L("lay","l2",1,"Edge. Gateway. Application. Data. And AI.","[Edge]. [Gateway]. [Application]. [Data]. And [AI].")
L("lay","l3",1,"Five layers, each with a narrow job. Client, edge, gateway, application, then data and AI.","Each layer has a [narrow job]. Client, edge, gateway, application, [data and AI].")

# ---------------- 2 who does what ----------------
L("org","o1",2,"The handbook's mental model is a company org chart, not one person doing everything.","A company [org chart], not one person doing [everything].")
L("org","o2",2,"The C D N is the receptionist. If they already have your answer, they hand it over right there.","The [CDN] is the receptionist: they hand over a [cached] answer.")
L("org","o3",2,"The gateway is security and routing. It checks your badge, then sends you to the right department.","The [gateway] checks your [badge], then [routes] you.")
L("org","o4",2,"The application service is that department, doing the real work. The database is the filing cabinet.","The [app] does the work. The [database] is the filing cabinet.")
L("org","o5",2,"The queue is the ticket system. The AI gateway talks to outside AI vendors.","The [queue] is the ticket system. The [AI gateway] talks to outside vendors.")

L("gw","g1",2,"Zoom in on the gateway: one front door, one address for web, mobile and partner clients.","The [gateway]: one [front door], one address.")
L("gw","g2",2,"It does the shared chores once: authenticate, rate limit, and route to the right private service.","[Authenticate], [rate limit], [route]. Once, for everyone.")
L("gw","g3",2,"Fail a check, and the request is rejected right there: a four zero one, or a four twenty nine. No service does any work.","Fail a check: [401] or [429]. No service does any work.")
L("gw","g4",2,"And it stays dumb. A gateway that also holds business logic stops being a gateway.","Keep it [dumb]. No [business logic] in the gateway.")

L("cache","c1",2,"The cache sits beside the app. Reads check it first.","The [cache] sits beside the app. Reads check it [first].")
L("cache","c2",2,"A hit comes back in about one millisecond. A miss reads the database, then saves the answer for next time.","A [hit]: about [1 ms]. A [miss]: read the database, [save] it.")
L("cache","c3",2,"On a write, the app updates the database and deletes the cached copy, so nobody reads stale data.","On a write: update the database, [delete] the cached copy.")

L("queue","q1",2,"The queue is for work that shouldn't make the client wait. Like sending a confirmation email.","The [queue] is for work the client shouldn't [wait] for.")
L("queue","q2",2,"The API validates the request, drops a job on the queue, and answers right away.","Validate, [enqueue], answer [right away].")
L("queue","q3",2,"Workers do the slow part later. If a worker crashes, the job goes back on the queue.","[Workers] do the slow part. A crash? The job [goes back].")
L("queue","q4",2,"That buys you decoupling, durability, and a steady pace when traffic spikes.","[Decoupling], [durability], steady pace in a [spike].")

L("ai","i1",2,"The AI gateway is one front door for every model call. Your apps never talk to a provider directly.","The [AI gateway]: one front door for [every] model call.")
L("ai","i2",2,"It handles authentication, rate limits, caching, routing and cost tracking once, for everyone. And if a provider is down, it falls back to another.","[Auth], [limits], [caching], [routing], [cost]. A provider down? [Fallback].")

# ---------------- 3 three requests ----------------
L("read","d1",3,"Request one, a simple read: GET slash products slash nine. It hits the C D N first.","Request one: [GET /products/9]. It hits the [CDN] first.")
L("read","d2",3,"If the C D N has the answer cached, it returns right there. Nothing behind it ever hears about the request.","[Cached] at the edge? Done. Nothing behind it [hears] about it.")
L("read","d3",3,"If not, the gateway authenticates and rate limits, then routes it to the application service.","Not cached: the [gateway] checks, then [routes] to the app.")
L("read","d4",3,"The app checks its cache. A hit skips the database. A miss queries it, then stores the result.","[Hit]: skip the database. [Miss]: query, then [store].")
L("read","d5",3,"Then the response retraces the same path, back to the client.","The response [retraces] the same path back.")

L("write","w1",3,"Request two, a write: POST slash orders. This is the handbook's end to end view of it.","Request two: [POST /orders]. The [end to end] view.")
L("write","w2",3,"A POST isn't cached, so it passes straight through to the application service.","A POST is [not cached]: it passes [straight through].")
L("write","w3",3,"The order service validates the body, commits to Post gress Q L in one transaction, updates Red iss, and publishes a message to the queue.","[Validate], [commit], update [Redis], [publish] a message.")
L("write","w4",3,"A two hundred one comes back in roughly twenty to one hundred fifty milliseconds. The worker sends the email after the response, so the client never waits.","[201] in about [20 to 150 ms]. The email goes out [after].")

L("chat","t1",3,"Request three, an AI chat message. The handbook traces it in seven steps.","Request three: [POST /chat]. Seven [steps].")
L("chat","t2",3,"The gateway validates the token and checks the rate limit. The app loads the conversation from Post gress Q L, and checks Red iss.","[Gateway]: token, rate limit. [App]: Postgres, Redis.")
L("chat","t3",3,"Then the app calls the AI gateway, which routes to an available provider, with a fallback if the primary is down.","The [AI gateway] routes to a provider, with a [fallback].")
L("chat","t4",3,"The answer streams back token by token, through the app and the gateway to the client.","The answer [streams] back, token by token.")
L("chat","t5",3,"And logging and cost tracking happen afterwards, through a queue, so they never slow the reply.","[Logging] and [cost] go through a [queue], after.")

L("sum","u1",3,"Same map, three different paths. A read can stop at the C D N. A write goes to the database and queues the slow work. A chat goes through the AI gateway.","Three [paths]. A read can [stop] at the CDN. A chat uses the [AI gateway].")

# ---------------- 4 see it run ----------------
L("route","v1",4,"Now let's watch the AI layer for real. This is the handbook's L L M gateway example, a small FastAPI app.","The handbook's [LLM gateway] example: a small [FastAPI] app.")
L("route","v1b",4,"Its setup is a few lines: providers in priority order, and a token bucket that allows five requests, refilling one per second.","[Providers] in priority order. A [token bucket]: five requests, [1/sec].")
L("route","v2",4,"Over the limit, the gateway answers four twenty nine. And every response gets a cost attached.","Over the limit: [429]. Every response gets a [cost].")

L("run1","e1",4,"Five calls to the same chat endpoint. Four were served by the first provider.","Five calls. Four served by the [first] provider.")
L("run1","e2",4,"On the fifth, it failed, and the gateway fell back to provider A, the only one that costs anything.","The fifth: it failed. The gateway fell [back] to provider A.")
L("run1","e3",4,"The usage endpoint rolls up cost per tenant: five requests, a fraction of a cent.","[Usage]: five requests, a fraction of a [cent].")

L("run2","f1",4,"Now a burst of eight requests. The first five pass. The next three get a four twenty nine: rate limited, right at the gateway.","A burst of eight: five [pass], three get [429].")

# ---------------- 5 don't over-build ----------------
L("simple","s1",5,"Now the most important rule. Not every API needs every layer. A small internal tool can be one application service with a database behind it, and that's the right architecture at that scale.","Not every API needs [every] layer. A small tool: [app] plus database. That's [right].")
L("simple","s3",5,"Each layer buys you something. A cache buys latency. A gateway buys central auth. A queue buys resilience. But the price is more moving parts, more failure modes, more to operate.","[Cache]: latency. [Gateway]: central auth. [Queue]: resilience. The [price]: complexity.")

L("x1","x1",5,"Mistake one. Assuming every API needs a gateway, a queue, and a cache from day one. Most don't, at first. Add a layer for a real problem, not a hypothetical one.","Mistake 1: every layer on [day one]. Add one for a [real] problem.")
L("x2","x2",5,"Mistake two. Treating microservices as automatically more production grade than a well built monolith. It depends on the problem. Part eleven covers it.","Mistake 2: [microservices] are not [automatically] better.")
L("x3","x3",5,"Mistake three. Bolting the AI layer on as an afterthought. It needs its own timeouts, fallbacks, and cost tracking.","Mistake 3: AI as an [afterthought]. It needs [timeouts], [fallbacks], [cost] tracking.")

L("aip","y1",5,"A database query is usually fast and predictable. A model call can be slow, non-deterministic, and billed by usage. That's why it deserves its own box.","A query is usually [fast]. A model call is [slow], [random], [metered].")
L("aip","y3",5,"So Parts fourteen to seventeen add L L M gateways, token rate limits, prompt caching, and semantic caching. Ideas a typical C R U D API never needed.","[LLM gateways], [token limits], [prompt caching], [semantic caching].")

# ---------------- 6 recap ----------------
L("rec","n1",6,"Let's recap.","Let's [recap].")
L("rec","n2",6,"A production API is a layered system: client, edge, gateway, application, then data and AI.","A layered system: client, edge, [gateway], [app], data and [AI].")
L("rec","n3",6,"Each layer has one narrow job, and requests take different paths through them.","One [narrow job] each. Different requests, different [paths].")
L("rec","n4",6,"Add a layer only for a real problem, and treat the AI layer like the database.","Add a layer only for a [real] problem. Treat the [AI layer] like the database.")
L("rec","n6",6,"And bookmark Part eighteen. It's the full production version of this map.","Bookmark [Part 18]: the full production map.")

L("quiz","z1",6,"Quick check before you go. A POST slash orders request must also send a confirmation email. How do you avoid making the client wait for it?","POST /orders must send an email. How do you not make the client [wait]?")
L("quiz","z2",6,"Pause and answer. Got it? Put the email on a queue as a background job. A worker sends it after the response.","Put it on a [queue]. A [worker] sends it [after] the response.")

L("out","p1",6,"Next up: the handbook's learning roadmap, a guided path through all twenty parts.","Next: the [learning roadmap] through all [20] parts.")
L("out","p2",6,"Or try the chapter's exercise: the layers a GET orders by I D request passes through, in a food delivery app.","Try it: layers for [GET /orders/{id}] in a [food delivery] app.")
L("out","p3",6,"Subscribe, and I'll see you in the next one.","[Subscribe], and see you in the next one.")
