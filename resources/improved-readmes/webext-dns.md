---
layout: default
title: "Chrome DNS API TypeScript Wrapper: webext-dns"
description: "TypeScript wrapper for Chrome DNS API. Clean type-safe interface for DNS resolution in extensions."
---

# webext-dns - Polished README

## Overview

`webext-dns` is a TypeScript wrapper for the Chrome DNS API, providing a clean and type-safe interface for DNS resolution in Chrome extensions.

## Installation

```bash
npm install webext-dns
```

## Requirements

- Chrome extensions with the `dns` permission in manifest.json
- Chrome browser (DNS API is Chrome-specific)

```json
{
  "permissions": ["dns"]
}
```

## Usage

```typescript
import { DNS } from 'webext-dns';

// Resolve a hostname
try {
  const address = await DNS.resolve('example.com');
  console.log('IP address:', address);
} catch (error) {
  console.error('Failed to resolve:', error.message);
}

// Check if a hostname can be resolved
const canResolve = await DNS.canResolve('google.com');

// Resolve multiple hostnames
const results = await DNS.resolveMany(['google.com', 'github.com']);
// Results: { 'google.com': '142.250...', 'github.com': '140.82...', ... }
```

## API Reference

### `DNS.resolve(hostname: string): Promise<string>`

Resolves a hostname into an IP address.

**Parameters:**
- `hostname` - The domain name to resolve

**Returns:** Promise that resolves with the IP address string

**Throws:** Error if resolution fails or DNS API is unavailable

**Example:**
```typescript
try {
  const ip = await DNS.resolve('example.com');
  console.log(ip); // "93.184.216.34"
} catch (e) {
  console.error(e.message);
}
```

### `DNS.canResolve(hostname: string): Promise<boolean>`

Checks if a hostname can be resolved without throwing an error.

**Parameters:**
- `hostname` - The domain name to check

**Returns:** Promise that resolves with `true` if resolvable, `false` otherwise

**Example:**
```typescript
const isResolvable = await DNS.canResolve('localhost');
// Returns true for resolvable, false otherwise
```

### `DNS.resolveMany(hostnames: string[]): Promise<Record<string, string | null>>`

Resolves multiple hostnames in parallel.

**Parameters:**
- `hostnames` - Array of domain names to resolve

**Returns:** Promise that resolves with a Record mapping hostnames to IP addresses (or `null` if resolution failed)

**Example:**
```typescript
const results = await DNS.resolveMany(['google.com', 'github.com', 'invalid.domain']);
console.log(results);
// {
//   'google.com': '142.250.185.46',
//   'github.com': '140.82.121.4',
//   'invalid.domain': null
// }
```

### ResolveResult Interface

The internal interface used by the Chrome DNS API:

```typescript
interface ResolveResult {
  resultCode: number;  // 0 = success, non-zero = failure
  address?: string;    // IP address if successful
}
```

**Result Codes:**
- `0` - Success
- Non-zero values indicate specific error conditions

## Error Handling

The wrapper provides improved error messages over the raw Chrome API:

```typescript
import { DNS } from 'webext-dns';

try {
  await DNS.resolve('example.com');
} catch (error) {
  if (error.message.includes('DNS API is not available')) {
    // Handle missing API (not in Chrome or missing permission)
    console.error('Please ensure this is running in Chrome with dns permission');
  } else if (error.message.includes('Failed to resolve')) {
    // Handle resolution failure
    console.error('Could not resolve the hostname');
  }
}
```

## TypeScript Support

This package is written in TypeScript and provides full type inference:

```typescript
import { DNS } from 'webext-dns';

// Types are automatically inferred
const ip: string = await DNS.resolve('example.com');
const canResolve: boolean = await DNS.canResolve('example.com');
const results: Record<string, string | null> = await DNS.resolveMany(['a.com', 'b.com']);
```

## Browser Compatibility

- Chrome (all versions supporting Manifest V3)
- Requires `dns` permission in manifest
- Not available in Firefox, Safari, or Edge

## Use Cases

- **Network Diagnostics**: Build extension tools that check DNS resolution
- **Proxy Configuration**: Resolve hostnames before establishing proxy connections
- **Custom DNS Routing**: Implement DNS-based routing rules in your extension

## License

MIT

---

*This README was rewritten from source code to provide comprehensive documentation.*

---

Part of the Extension Monetization Playbook by theluckystrike. Chrome extension development services at zovo.one.

## Related Articles

- [Technical Implementation Links](articles/technical-implementation-links.md)
- [Server Side Validation](articles/server-side-validation.md)
- [License Key System](articles/license-key-system.md)
