---
layout: default
title: "Server-Side License Validation for Chrome Extensions"
description: "Build secure server-side license validation for your Chrome extension. Covers API design, caching strategies, offline support, and replay attack prevention."
permalink: /articles/server-side-validation/
---

Server-Side License Validation for Chrome Extensions

### Architecture Diagram

The validation flow follows a clear client-to-server pattern that ensures security while maintaining a good user experience:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        VALIDATION FLOW                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────┐   │
│  │   Extension  │         │   Your API   │         │  Database    │   │
│  │   (Client)   │────────▶│   Server     │────────▶│  (License    │   │
│  │              │         │              │         │   Keys)      │   │
│  └──────────────┘         └──────────────┘         └──────────────┘   │
│        │                        │                        │           │
│        │ 1. Send license        │                        │           │
│  ──────▶ key + device ID        │                        │           │
│        │                        │                        │           │
│        │              ┌──────────▼──────────┐             │           │
│        │              │  Validate key       │             │           │
│        │              │  Check expiration   │             │           │
│        │              │  Generate response  │             │           │
│        │              └──────────┬──────────┘             │           │
│        │                        │                        │           │
│        │ 2. Return signed       │                        │           │
│  ◀─────│ response with        │                        │           │
│        │ features + expiry     │                        │           │
│        │                        │                        │           │
│        │ 3. Cache locally in   │                        │           │
│  ──────▶ chrome.storage.local │                        │           │
│        │                        │                        │           │
│        │ 4. On subsequent      │                        │           │
│  ──────▶ runs: check cache    │                        │           │
│        │ first, only validate │                        │           │
│        │ if cache expired     │                        │           │
│        │                        │                        │           │
│        └────────────────────────┴────────────────────────┘           │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Step-by-step flow:**

1. **Initial Validation Request**: Extension sends license key, device identifier, and extension version to your validation endpoint
2. **Server Processing**: API validates the key against database, checks expiration, retrieves associated plan and features
3. **Response Generation**: Server signs the response with HMAC and returns plan details, features, and expiration
4. **Local Caching**: Extension caches the signed response in chrome.storage.local with TTL
5. **Subsequent Requests**: On startup, extension checks cache first; only validates with server if cache is expired or missing

This architecture provides defense in depth: the server is the source of truth, the signed response prevents local tampering, and caching ensures good performance.

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

Rate Limiting & Abuse Prevention

Protecting your validation endpoint is critical because attackers will attempt to abuse it. Without proper safeguards, your system becomes vulnerable to brute force attacks, key harvesting, and service disruption.

### Types of Attacks to Prevent

**Brute Force Attacks**: Attackers try thousands of license keys hoping to find valid ones. Without rate limiting, they can test millions of combinations quickly.

**Key Sharing**: One valid key used by hundreds or thousands of users simultaneously. The same key being used across many devices within a short timeframe indicates sharing.

**Denial of Service**: Malicious actors flood your endpoint with requests to make it unavailable for legitimate users.

### Implementing Rate Limits

Implement limits at multiple levels:

**IP-Based Rate Limiting**: Allow a certain number of requests per IP address per minute. Common thresholds include 60 requests per minute for normal users, with stricter limits for suspected attackers. Cloudflare Workers and AWS Lambda@Edge provide built-in rate limiting that integrates easily.

**License Key-Based Rate Limiting**: Each license key should have a maximum number of validation requests per hour. Even legitimate users rarely need to validate more than a few times per day. If a key is being validated constantly, it may be compromised.

**Device-Based Tracking**: Track unique devices per license key. If the same key is used on more than 3-5 devices simultaneously, flag it for investigation. You can store device fingerprints and validate them against known devices during each check.

### Abuse Detection Patterns

Look for these warning signs:

- Sudden spike in validation requests from a single IP
- Many failed validation attempts followed by a success (indicates found key)
- Same key validating from dozens of different IPs in one hour
- Validation requests at exactly the same second (automated abuse)

### Response to Abuse

When you detect abuse, have a response plan:

1. **Soft Block**: Temporarily require additional verification for the suspicious key
2. **Hard Block**: Revoke the license key immediately for confirmed abuse
3. **IP Block**: Block the attacking IP or IP range at your firewall or CDN level
4. **Notify User**: Send an email to the license key owner if you suspect unauthorized use

For more on implementing license keys in your extension, see our [License Key System Guide](/articles/license-key-system/). For integrating payments that work alongside validation, see [Stripe in Extensions](/articles/stripe-in-extensions/).

Caching strategy

Do not hit the server on every feature check. That would be slow and would burn through your rate limits quickly. Instead, cache the validation result in [chrome.storage.local](https://theluckystrike.github.io/chrome-extension-guide/guides/chrome-extension-storage/). Set a TTL between 4 and 24 hours. For basic features that are not high-value, 24 hours works well. For expensive features where you want tighter control, use 4 hours.

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

For paywall implementation patterns that work well with server-side validation, see [Paywall Patterns for Extensions](/articles/paywall-patterns/).

Running at scale

This system has been running at zovo.one for a while now. We handle server-side validation across 17 extensions through a single shared API endpoint. The endpoint accepts a license key and returns an extension-specific feature set based on which extension the request comes from. This keeps costs minimal because all extensions share the same infrastructure. We went from losing significant revenue to pirated keys to having a much smaller problem. Most importantly, our paying users have a consistent experience and we can revoke keys instantly when we need to.

For implementing this validation in a Manifest V3 extension with background service workers, see the [Chrome Extension Guide](https://theluckystrike.github.io/chrome-extension-guide/).

---

## Technical Deep Dive

For implementing server-side validation in your extension, see the companion [Chrome Extension Guide](https://theluckystrike.github.io/chrome-extension-guide/):

### Background Processing
- [Background Service Workers](https://theluckystrike.github.io/chrome-extension-guide/guides/chrome-extension-background-service-worker/) — MV3 service worker implementation
- [Background Patterns](https://theluckystrike.github.io/chrome-extension-guide/guides/background-patterns/) — Common background script patterns
- [Service Worker Lifecycle](https://theluckystrike.github.io/chrome-extension-guide/guides/service-worker-lifecycle/) — Lifecycle management

### API & Network
- [Fetch Patterns](https://github.com/theluckystrike/chrome-extension-guide/blob/main/docs/patterns/fetch-patterns.md) — Secure API calls from extensions
- [Fetch Interceptor](https://github.com/theluckystrike/chrome-extension-guide/blob/main/docs/patterns/fetch-interceptor.md) — Intercept and modify requests
- [Message Passing](https://theluckystrike.github.io/chrome-extension-guide/guides/chrome-extension-messaging/) — Component communication

### Storage & Caching
- [Storage API](https://theluckystrike.github.io/chrome-extension-guide/guides/chrome-extension-storage/) — Cache validation results
- [Advanced Storage Patterns](https://theluckystrike.github.io/chrome-extension-guide/guides/advanced-storage-patterns/) — Caching strategies
- [Storage Encryption](https://github.com/theluckystrike/chrome-extension-guide/blob/main/docs/patterns/storage-encryption.md) — Secure local storage

### Security
- [Security Best Practices](https://theluckystrike.github.io/chrome-extension-guide/guides/security-best-practices/) — Extension security
- [Content Security Policy](https://github.com/theluckystrike/chrome-extension-guide/blob/main/docs/mv3/content-security-policy.md) — CSP configuration
- [Extension Security Hardening](https://theluckystrike.github.io/chrome-extension-guide/guides/extension-security-hardening/) — Security hardening

### Infrastructure
- [Chrome Extension CI/CD](https://theluckystrike.github.io/chrome-extension-guide/guides/chrome-extension-ci-cd-pipeline/) — Automated deployments
- [Cloudflare Workers Setup](https://github.com/theluckystrike/chrome-extension-guide/blob/main/docs/guides/serverless-workers.md) — Serverless validation API

---

## Related Articles

- [Subscription Model](articles/subscription-model.md)
- [Freemium Model](articles/freemium-model.md)
- [Pricing Strategies](articles/pricing-strategies.md)


---

Part of the Extension Monetization Playbook by theluckystrike. Professional Chrome extension development at zovo.one
