---
title: "Server-Side License Validation for Chrome Extensions"
description: "The problem with client-side-only validation If you rely only on client-side checks, your validation is broken by design. Any user can open DevTools, find the v"
permalink: /server-side-license-validation-for-chrome-extensions
layout: default
---

The problem with client-side-only validation

If you rely only on client-side checks, your validation is broken by design. Any user can open DevTools, find the validation function, and bypass it in a few minutes. They might comment out the license check or modify the response. This only stops honest users who never thought to look. The reality is that determined users will bypass client-side validation every single time. This is why you need server-side validation as your source of truth.

Some developers think obfuscation helps here. It does not. A determined user will reverse engineer your obfuscated code given enough time. Obfuscation adds complexity for the attacker but nothing fundamental. The only real defense is moving the validation logic entirely to your server where the user has no access.

The basic architecture

Your extension sends a license key or token to your API on startup. The server checks the database to verify the key is valid and retrieves the associated plan and feature set. It returns something like { plan: "pro", features: ["export", "api"], expiresAt: "2025-06-01" }. The extension caches this locally with an expiration timestamp. On subsequent startups, the extension checks the cache first. Only on a cache miss or expiration does it hit the server again. This happens invisibly in the background.

The request from your extension should include several pieces of information. Send the license key, the extension version, and a unique device identifier. The device identifier helps you detect unusual patterns like the same key being used on hundreds of different devices simultaneously. This is often a sign of key sharing or a leaked key.

Building the validation endpoint

Create a simple REST endpoint that accepts a POST request with the license key. The response is JSON containing the plan name, enabled features, and expiration timestamp. This endpoint must run over HTTPS. There is no exceptions here. Sending license keys over plain HTTP is a security hole you cannot afford.

A typical response looks like this for a valid key:
```
{
  "valid": true,
  "plan": "pro",
  "features": ["export", "api", "unlimited-reports"],
  "expiresAt": "2025-06-01T00:00:00Z",
  "issuedAt": "2025-01-15T14:32:00Z",
  "nonce": "abc123xyz"
}
```

And for an invalid or expired key:
```
{
  "valid": false,
  "plan": "free",
  "features": ["basic-export"],
  "error": "key_expired"
}
```

Rate limiting is critical. Implement limits by IP address and by license key. Without rate limiting, attackers can brute force valid keys. Most serverless platforms like Cloudflare Workers provide built-in rate limiting. If you self-host, you need to implement this yourself or use a reverse proxy with rate limiting built in.

Caching strategy

Do not hit the server on every feature check. That would be slow and would burn through your rate limits quickly. Instead, cache the validation result in chrome.storage.local. Set a TTL between 4 and 24 hours. For basic features that are not high-value, 24 hours works well. For expensive features where you want tighter control, use 4 hours.

The cache should store the complete server response including the signature. Store the expiration time separately so your extension can quickly check if the cache is stale without parsing the full response. Use chrome.storage.local.set with an object like { licenseData: { ... }, cachedAt: timestamp }.

When the cache expires or is empty, the extension makes a fresh request to the server. You need to decide between fail open and fail closed behavior. Fail open means that if the validation server is unreachable, the extension grants access based on the cached data. Fail closed means the extension denies access until the server responds. I prefer fail open because your users should not lose access to features they paid for just because your server had a brief outage. That said, fail closed makes sense for high-value enterprise features where the cost of abuse is high.

Handling offline scenarios

Users go offline on planes and trains. They lose internet in elevators and remote areas. A generous TTL of 24 to 72 hours handles most offline scenarios without any server contact. The cached data should include a signed token from the server. When the server signs the response with a secret key and includes the expiration in the payload, users cannot simply edit chrome.storage.local to grant themselves premium access. The extension verifies the signature before trusting the cached data.

This approach supports truly offline-first extensions. The signed token embeds the expiration so the extension knows when the data is stale. As long as the signature is valid and the embedded expiration has not passed, the cached data is trustworthy.

The signature should use HMAC-SHA256. The server signs the JSON response by creating a string representation and computing HMAC-SHA256 with your secret key. The extension does the same calculation and compares. If they match, the data has not been tampered with.

Preventing replay attacks

Someone could intercept a valid API response and replay it later. This is a replay attack. You prevent this by including a nonce or timestamp in the request. The server includes an issuedAt timestamp in the response. The extension checks that the response is recent, within the last few minutes. If someone tries to replay an old response, the timestamp check fails and the extension requests fresh data.

Use short-lived tokens that require periodic refresh. This limits the window of opportunity for replay attacks. When combined with signed responses and timestamp validation, you have defense in depth against this attack vector.

Infrastructure options and costs

You have several choices for hosting the validation API. A simple Node.js or Python backend on a $5 VPS from DigitalOcean or Linode works if you want full control. You will need to handle SSL yourself, which means setting up LetsEncrypt and renewals.

Cloudflare Workers or AWS Lambda provide serverless execution. These cost almost nothing for moderate traffic and include SSL automatically. This is the path I recommend for most extension developers. You focus on writing the code, not managing servers. Cloudflare Workers are particularly attractive because the free tier handles up to 100,000 requests per day. If you have fewer than 10,000 paying users all validating at once, you stay in the free tier. Even at 100,000 daily requests, the cost is only $5 per month.

For the database, PlanetScale or Supabase work well. Both offer managed databases without server maintenance. Supabase has the advantage of a built-in REST API that you can query directly from Cloudflare Workers. This reduces the number of moving parts you need to maintain. The Supabase free tier includes 500MB database storage and 2GB bandwidth, which is plenty for license validation.

If you need simpler storage, consider Redis through Upstash. It integrates naturally with Cloudflare Workers via HTTP and pricing starts at free with 10,000 commands per day. Redis is excellent for rate limiting counters and quick validation lookups.

Running at scale

This system has been running at zovo.one for a while now. We handle server-side validation across 17 extensions through a single shared API endpoint. The endpoint accepts a license key and returns an extension-specific feature set based on which extension the request comes from. This keeps costs minimal because all extensions share the same infrastructure. We went from losing significant revenue to pirated keys to having a much smaller problem. Most importantly, our paying users have a consistent experience and we can revoke keys instantly when we need to.
