# (beat, key, chapter, say, cap)   cap: [brackets] = highlighted keywords
CHAPTERS = {
  0: "Intro",
  1: "The contract",
  2: "A request, line by line",
  3: "The server side",
  4: "Who calls APIs",
  5: "Five mistakes",
  6: "Recap",
}
B = []
def L(beat, key, ch, say, cap): B.append(dict(beat=beat, key=key, ch=ch, say=say, cap=cap))

L("hook","h1",0,"Your app talks to a server you'll never see.","Your app talks to a [server] you'll never see.")
L("hook","h2",0,"What exactly is it saying? And why do you never need to know how that server works?","What is it [saying]? Why don't you need to know how it [works]?")
L("hook","h3",0,"That's an A P I. By the end of this video, you'll read one, run one, and spot the mistakes that break them.","That's an [API]. You'll [read] one, [run] one, and spot the [mistakes].")

L("road","r1",0,"Here's the plan, in five parts.","Here's the plan, in [five] parts.")
L("road","r2",0,"One, the contract. Two, a request, line by line. Three, the server side.","[Contract]. [Request]. [Server side].")
L("road","r3",0,"Four, who calls APIs. And five, the mistakes that break them.","[Callers]. And the [mistakes] that break them.")

L("c1a","a1",1,"API stands for Application Programming Interface. Strip away the acronym, and it's a contract.","API: Application Programming Interface. Strip the acronym: a [contract].")
L("c1a","a2",1,"One program asks another program to do something, without knowing how it gets done inside.","One program [asks] another to do something, without knowing [how].")
L("c1a","a3",1,"The handbook's glossary puts it the same way: a defined contract, with no need to know the implementation.","The handbook glossary: a [defined contract], no need to know the [implementation].")

L("c1b","b1",1,"Think of a wall socket. You plug in a lamp, and you know nothing about the power station.","Think of a wall [socket]. You know nothing about the power [station].")
L("c1b","b2",1,"The shape of the socket is the promise.","The shape of the socket is the [promise].")

L("c1c","c1",1,"Or think of a restaurant. You read the menu, you tell the waiter what you want, and the kitchen cooks it.","A restaurant: [menu], [waiter], [kitchen].")
L("c1c","c2",1,"You never see the kitchen. It can swap chefs, change the stove, even rewrite the recipe.","The kitchen can swap [chefs], change the [stove], rewrite the [recipe].")
L("c1c","c3",1,"As long as the dish matches the menu, you never notice.","As long as the dish matches the [menu], you never notice.")
L("c1c","c4",1,"That's the whole value of an API. Both sides can change independently, as long as the contract holds.","Both sides can [change independently], as long as the contract [holds].")

L("c2a","d1",2,"This handbook focuses on web APIs. A client sends an HTTP request, and a server sends back a response.","Web APIs: a [client] sends a [request], a [server] sends a [response].")
L("c2a","d2",2,"The client is anything that starts the conversation. A browser, a phone app, another service, a script.","The client is anything that [starts] the conversation.")
L("c2a","d3",2,"M D N puts it plainly: the client always initiates. The server never does.","MDN: the client always [initiates]. The server never does.")

L("c2b","e1",2,"Here's a real request. GET, slash users, slash forty-two.","A real request: [GET /users/42]")
L("c2b","e2",2,"GET is the method. It says what you want to do. The path says which thing you want.","The [method] says what to do. The [path] says which thing.")
L("c2b","e3",2,"Headers add context. Accept says you want JSON. Authorization says who you are.","[Headers] add context: what you accept, who you are.")

L("c2b2","e4",2,"Every HTTP message, request or response, has the same shape: a start line, headers, an empty line, and an optional body.","Same shape: a [start line], [headers], an empty line, a [body].")

L("c2c","f1",2,"The server answers with a status code. Two hundred means OK.","The server answers with a [status code]. [200] means OK.")
L("c2c","f3",2,"Then comes the body, in JSON. An id, a name, an email.","Then the [body], in [JSON]: an id, a name, an email.")
L("c2c","f4",2,"Nothing in this response says whether the data came from Post gress Q L, Mongo D B, or a plain dictionary. That's the point.","Nothing says if the data came from [PostgreSQL], [MongoDB] or a [dictionary].")
L("c2e","f2",2,"Status codes come in families. Two hundreds mean success. Four hundreds mean the caller made a mistake. Five hundreds mean the server did.","[2xx] success. [4xx] the caller erred. [5xx] the server erred.")

L("c2d","g1",2,"One more thing from M D N. HTTP is stateless. Every request stands alone, so the server doesn't remember the last one unless you send something that identifies you.","HTTP is [stateless]. Every request stands [alone].")

L("c3m","q1",3,"Now zoom out. Here is the whole trip, drawn in the handbook as a sequence diagram.","Zoom out: the whole [trip], as a [sequence diagram].")
L("c3m","q2",3,"The client sends a request. The API matches the route and validates it.","[Request] in. [Route matched], request [validated].")
L("c3m","q3",3,"Server logic fetches data from the database, and the result travels back as a response.","[Fetch] data. The [result] travels back as a [response].")
L("c3m","q4",3,"The client only ever depends on the API on the left. Everything to the right is free to change.","The client depends on the [API]. The rest is free to [change].")

L("c3a","i1",3,"Now the other side. This is a complete API endpoint, written in FastAPI, the framework this handbook builds with.","The provider side: a complete endpoint in [FastAPI].")
L("c3a","i2",3,"One decorator maps GET, slash users, slash user id, to a Python function.","One [decorator] maps a [route] to a [function].")
L("c3a","i3",3,"The function looks the user up. If there's no such user, it raises a four zero four.","No such user? It raises a [404].")
L("c3a","i4",3,"And because user id is typed as an integer, FastAPI rejects anything else before your code even runs.","Typed as an [int]: bad input is rejected [before] your code runs.")

L("c3b","j1",3,"Run it, and ask for user forty-two.","Run it. Ask for user [42].")
L("c3b","j2",3,"You get the status line, the headers, and the JSON.","[Status line], [headers], [JSON].")
L("c3b","j3",3,"Ask for a user that doesn't exist, and you get a four zero four. Ask for the word banana, and you get a four twenty two.","Missing user: [404]. The word banana: [422].")

L("c3c","k1",3,"Today that dictionary is fake. Next week it could be Post gress Q L, or a call to another service.","Today a fake [dictionary]. Next week [PostgreSQL].")
L("c3c","k2",3,"Not one line the client depends on changes. Same URL, same JSON shape, same status codes.","Same [URL], same [JSON shape], same [status codes].")
L("c3c","k3",3,"That is the contract doing its job.","That is the [contract] doing its job.")

L("c4a","l1",4,"Who calls APIs? More than you think.","So who calls APIs? [More] than you think.")
L("c4a","l2",4,"Your weather app. The sign in with Google button. A payment form. Another backend service.","Weather app. Sign in with Google. Payments. Other [services].")
L("c4a","l3",4,"And now, AI. Every call to a language model through code is a web API: a POST request with a JSON body, and JSON coming back.","A language model call is a [POST] with a [JSON] body.")

L("c4b","m1",4,"Same contract. The kitchen is just a very large model you will never see inside.","Same contract. The kitchen is a [model] you never see.")
L("c4b","m2",4,"Postman's twenty twenty-five survey of over fifty-seven hundred developers found that eighty-nine percent use generative AI.","Postman's 2025 survey: [89%] use generative AI.")
L("c4b","m3",4,"But only twenty-four percent design their APIs with AI agents in mind.","Only [24%] design APIs with AI agents in mind.")
L("c4b","m4",4,"The same survey found sixty-five percent of organizations earn revenue from their APIs. Contracts are products.","[65%] of organizations earn revenue from APIs.")

L("m1","x1",5,"Mistake one. Saying API when you mean REST API. APIs also include function signatures and operating system calls. REST is one architectural style for web APIs.","Mistake 1: API [is not] REST API.")
L("m2","x2",5,"Mistake two. Copying your database columns straight into your responses. Rename a column, and every client breaks. Design the contract first, then the code behind it.","Mistake 2: mirroring your [database] in responses.")
L("m3","x3",5,"Mistake three. Returning two hundred OK for everything, even errors. The status code is part of the contract. Use it.","Mistake 3: [200 OK] for everything, even errors.")
L("m4","x4",5,"Mistake four. Confusing the API with the whole system, or with the user interface. A UI consumes an API. One API can serve a website and a mobile app.","Mistake 4: the API is not the [system] or the [UI].")
L("m5","x5",5,"And mistake five. Leaving the contract undocumented. If callers have to reverse engineer your behavior, it's not a contract. Part three of the handbook covers OpenAPI for exactly this.","Mistake 5: an [undocumented] contract.")

L("rec","n1",6,"Let's recap.","Let's [recap].")
L("rec","n2",6,"An API is a contract between two programs.","An API is a [contract] between two programs.")
L("rec","n3",6,"A web API is an HTTP request and a response.","A web API is a [request] and a [response].")
L("rec","n4",6,"The server behind it is free to change.","The server behind it is free to [change].")
L("rec","n5",6,"Anyone can be the caller, even an AI model.","Anyone can call it, even an [AI model].")
L("rec","n6",6,"And your job is to protect the contract.","Your job: [protect] the contract.")

L("out","o1",6,"Next up, Part one of the handbook: how the internet actually works.","Next: how the [internet] actually works.")
L("out","o2",6,"Before you go, try the chapter's exercise: add a GET slash users endpoint, and decide what it should return when the database is empty.","Try it: a [GET /users] endpoint. What if the database is [empty]?")
L("out","o3",6,"Subscribe, and I'll see you in the next one.","[Subscribe], and see you in the next one.")
