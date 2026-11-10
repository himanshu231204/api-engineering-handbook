# Script — What Is an API? (long)

Runtime 06:07. Chapters:

- 00:00 Intro: what is an API?
- 00:26 The contract
- 01:19 A request, line by line
- 02:38 The server side
- 03:39 Who calls APIs
- 04:28 Five mistakes
- 05:31 Recap and what's next


## Intro

- **00:00** Your app talks to a server you'll never see.
- **00:02** What exactly is it saying? And why do you never need to know how that server works?
- **00:07** That's an API. By the end of this video, you'll read one, run one, and spot the mistakes that break them.
- **00:14** Here's the plan, in five parts.
- **00:16** One, the contract. Two, a request, line by line. Three, the server side.
- **00:21** Four, who calls APIs. And five, the mistakes that break them.

## The contract

- **00:27** API stands for Application Programming Interface. Strip away the acronym, and it's a contract.
- **00:34** One program asks another program to do something, without knowing how it gets done inside.
- **00:40** The handbook's glossary puts it the same way: a defined contract, with no need to know the implementation.
- **00:47** Think of a wall socket. You plug in a lamp, and you know nothing about the power station.
- **00:53** The shape of the socket is the promise.
- **00:55** Or think of a restaurant. You read the menu, you tell the waiter what you want, and the kitchen cooks it.
- **01:01** You never see the kitchen. It can swap chefs, change the stove, even rewrite the recipe.
- **01:07** As long as the dish matches the menu, you never notice.
- **01:11** That's the whole value of an API. Both sides can change independently, as long as the contract holds.

## A request, line by line

- **01:20** This handbook focuses on web APIs. A client sends an HTTP request, and a server sends back a response.
- **01:29** The client is anything that starts the conversation. A browser, a phone app, another service, a script.
- **01:36** MDN puts it plainly: the client always initiates. The server never does.
- **01:42** Here's a real request. GET /users/42.
- **01:46** GET is the method. It says what you want to do. The path says which thing you want.
- **01:52** Headers add context. Accept says you want JSON. Authorization says who you are.
- **01:58** The server answers with a status code. 200 means OK.
- **02:02** Status codes come in families. 200s mean success. 4xx mean the caller made a mistake. 5xx mean the server did.
- **02:12** Then comes the body, in JSON. An id, a name, an email.
- **02:17** Nothing in this response says whether the data came from PostgreSQL, MongoDB, or a plain dictionary. That's the point.
- **02:26** One more thing from MDN. HTTP is stateless. Every request stands alone, so the server doesn't remember the last one unless you send something that identifies you.

## The server side

- **02:40** Now the other side. This is a complete API endpoint, written in FastAPI, the framework this handbook builds with.
- **02:48** One decorator maps GET /users/{user_id} to a Python function.
- **02:54** The function looks the user up. If there's no such user, it raises a 404.
- **03:00** And because user id is typed as an integer, FastAPI rejects anything else before your code even runs.
- **03:08** Run it, and ask for user 42.
- **03:10** You get the status line, the headers, and the JSON.
- **03:14** Ask for a user that doesn't exist, and you get a 404. Ask for the word banana, and you get a 422.
- **03:22** Today that dictionary is fake. Next week it could be PostgreSQL, or a call to another service.
- **03:29** Not one line the client depends on changes. Same URL, same JSON shape, same status codes.
- **03:36** That is the contract doing its job.

## Who calls APIs

- **03:40** Who calls APIs? More than you think.
- **03:43** Your weather app. The sign in with Google button. A payment form. Another backend service.
- **03:49** And now, AI. Every call to a language model through code is a web API: a POST request with a JSON body, and JSON coming back.
- **04:00** Same contract. The kitchen is just a very large model you will never see inside.
- **04:06** Postman's twenty twenty-five survey of over fifty-seven hundred developers found that eighty-nine percent use generative AI.
- **04:15** But only twenty-four percent design their APIs with AI agents in mind.
- **04:20** The same survey found sixty-five percent of organizations earn revenue from their APIs. Contracts are products.

## Five mistakes

- **04:30** Mistake one. Saying API when you mean REST API. APIs also include function signatures and operating system calls. REST is one architectural style for web APIs.
- **04:44** Mistake two. Copying your database columns straight into your responses. Rename a column, and every client breaks. Design the contract first, then the code behind it.
- **04:56** Mistake three. Returning 200 OK for everything, even errors. The status code is part of the contract. Use it.
- **05:04** Mistake four. Confusing the API with the whole system, or with the user interface. A UI consumes an API. One API can serve a website and a mobile app.
- **05:17** And mistake five. Leaving the contract undocumented. If callers have to reverse engineer your behavior, it's not a contract. Part three of the handbook covers OpenAPI for exactly this.

## Recap

- **05:33** Let's recap.
- **05:34** An API is a contract between two programs.
- **05:37** A web API is an HTTP request and a response.
- **05:42** The server behind it is free to change.
- **05:44** Anyone can be the caller, even an AI model.
- **05:48** And your job is to protect the contract.
- **05:51** Next up, Part one of the handbook: how the internet actually works.
- **05:55** Before you go, try the chapter's exercise: add a GET /users endpoint, and decide what it should return when the database is empty.
- **06:04** Subscribe, and I'll see you in the next one.
