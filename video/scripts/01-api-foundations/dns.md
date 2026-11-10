---
chapter: docs/01-api-foundations/dns.md
part: 1
index: 5
title: DNS
target_seconds: 450
reviewed: true
---

## Hook

[scene: Title]

You never type an IP address into your API client. You type a name. So who turns that name into a number, and why does it break so often in production? DNS turns a name like api dot example dot com into an IP address through a cached chain of servers. And a single setting, the TTL, controls how long every answer gets reused. Let's walk through it.

## Why It Matters

Somewhere between typing api dot stripe dot com and your request leaving your machine, a human-readable name has to become the numeric IP address that routing understands. That translation is DNS. It is also a surprisingly common cause of production incidents. When someone says the API is down, it is very often that DNS didn't resolve, or that DNS is returning a stale IP. It is not an application bug at all. As an API developer, you will configure DNS records for your own services, and you will need to reason about DNS failures in the systems you consume.

## Concept

[scene: Concept heading="Names to numbers" body="DNS maps api.example.com to 93.184.216.34"]
[scene: Concept heading="Distributed, hierarchical, cached" body="No single server holds every mapping. Answers are cached for their TTL."]
[scene: Concept heading="Record types you will meet" body="A · AAAA · CNAME · TXT · NS"]

DNS, the Domain Name System, is the internet's naming system. It maps a domain name, like api dot example dot com, to an IP address, like 93 dot 184 dot 216 dot 34. Think of the contacts app on your phone, turning a person's name into their number.

Three words describe it. Distributed: no single server holds every mapping in the world, so the work is split across a hierarchy of servers. Hierarchical: a name reads right to left in authority. First the root, then the top-level domain, like dot com, then the domain itself, then any subdomains. And cached at every level: answers are saved, with an expiry called the TTL, by resolvers, operating systems and even browsers.

Picture directory assistance. You ask your local operator, your ISP's resolver, for a number. They don't know it, but they know which regional office to call, and that office knows which local office to ask. Then the operator writes the answer on a sticky note with an expiry date, so the next callers get it instantly.

As an API developer you will meet a few record types. A maps a name to an IPv4 address. AAAA does the same for IPv6. A CNAME is an alias that points to another hostname, for example your API name pointing at a cloud load balancer. TXT holds text, such as domain ownership checks. And NS says which nameservers are authoritative for the domain.

## How It Works

[scene: DiagramWalk svg=01-dns-resolution.svg steps=1-7]

Here is a lookup for api dot example dot com, step by step.

Step one. Your device checks its own cache, at the operating system level and sometimes in the browser. If it already knows the answer and the TTL hasn't expired, it's done immediately, and the rest of the chain never happens.

Step two. If nothing is cached, your device asks a recursive resolver to do the work for it. That is usually run by your ISP, or a public service like 8 dot 8 dot 8 dot 8 or 1 dot 1 dot 1 dot 1.

Step three. The resolver asks a root server: who handles dot com? The root server doesn't know the final answer. It points to the dot com servers.

Step four. The resolver asks the dot com TLD server about example dot com, and gets pointed onward again, this time to the nameserver for example dot com.

Step five. That is the authoritative nameserver, the one that actually holds the real records. It answers with the A record, or the AAAA record for IPv6: the IP address for api dot example dot com.

Step six. The IP address travels back to your device. Only now can the TCP, TLS and HTTP flow begin.

Step seven. Every answer is cached for its TTL, for example 300 seconds, by the resolver and by your device. That is why steps three to five are skipped most of the time.

## Demo

[scene: Terminal title=dig lines="dig api.example.com A|;; ANSWER SECTION:|api.example.com.    300    IN    A    93.184.216.34|;; Query time: 24 msec|;; SERVER: 1.1.1.1#53"]
[scene: CodeReveal lang=python lines="import socket|# This performs a DNS lookup and returns the resolved IPv4 address.|ip_address = socket.gethostbyname(hostname)|# getaddrinfo gives the fuller picture: multiple addresses (A and AAAA),|results = socket.getaddrinfo(hostname, 443, proto=socket.IPPROTO_TCP)"]

You can watch this yourself with dig. The query asks for the A record of api dot example dot com. The answer section shows the record: the name, a TTL of 300, the record type A, and the IP address. The 300 is the TTL in seconds, how long resolvers should cache this answer before asking again. The last lines show the lookup took 24 milliseconds, answered by the resolver at 1 dot 1 dot 1 dot 1. This single lookup happens before a single byte of your HTTP request is sent.

Python exposes the same step through the socket module. gethostbyname performs a DNS lookup and returns the IPv4 address. Every requests dot get call does this internally before opening a TCP connection. getaddrinfo gives the fuller picture: a domain can resolve to more than one IP, both IPv4 and IPv6, for redundancy and load balancing, so you can loop over the results. And if gethostbyname raises a gaierror, that is DNS resolution failing. It is a different failure from a TCP timeout or an HTTP error, so learn to recognise it.

## Mistakes

[scene: Mistakes items="Blaming the application for a DNS failure|Leaving a high TTL before a migration|Hardcoding IP addresses instead of hostnames"]

Three mistakes to avoid. First, confusing a DNS failure with an application failure. Could not resolve host is a DNS or TCP-level problem, so check dig or nslookup before you dig through application logs. Second, forgetting to lower the TTL before a planned migration. Resolvers keep the old answer until it expires, so some clients keep hitting the old server for hours, or days. Third, hardcoding IP addresses. That bypasses DNS entirely and breaks the moment the server's IP changes.

In production, remember that TTL is a trade-off. A low TTL lets you fail over quickly but means more lookups. A high TTL means fewer lookups, but a bad record can stay cached and broken for a long time. And if your authoritative nameservers go down, your API is unreachable even when your servers are perfectly healthy, so use a redundant DNS provider.

## Recap

[scene: Recap items="DNS maps names to IPs through root, TLD and authoritative servers|Record types: A, AAAA, CNAME, TXT, NS|TTL trades fast change against fewer lookups|When connectivity breaks, rule out DNS first"]
[scene: Quiz q1="Which server holds the real records for example.com, and which servers point the resolver towards it?" a1="The authoritative nameserver holds them. The root server points to the .com TLD server, which points to the authoritative nameserver." q2="What happens if you move api.yourcompany.com to a new IP while its record has a 24-hour TTL?" a2="Caches keep the old IP until their copy expires, for up to a day. Lower the TTL well before the move." q3="Your Python client raises socket.gaierror. Which layer failed, and what do you check first?" a3="DNS resolution failed, so no TCP connection was tried. Check the name with dig or nslookup first."]

To recap. DNS translates names into IP addresses through a cached chain: resolver, root, TLD and authoritative nameserver. The record types you will configure are A, AAAA, CNAME, TXT and NS. TTL is the trade-off between fast changes and fewer lookups. And when connectivity breaks, rule out DNS first.

Now check yourself. One: which server holds the real records for a domain, and which servers point the resolver towards it? Two: what happens if you move a server to a new IP while its record has a 24-hour TTL? Three: your Python client raises a gaierror. Which layer failed, and what do you check first? Pause and answer before the answers appear.

## Next

[scene: Concept heading="Next: URLs" body="Part 1, video 6"]

You now know how a name becomes an address. Next up is the URL: its six parts, and why the fragment never leaves the client. See you in the next video.
