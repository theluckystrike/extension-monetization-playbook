---
layout: default
title: "How to Integrate Stripe Payments in Chrome Extensions"
description: "Step-by-step guide to adding Stripe Checkout, webhooks, and subscription management to your Chrome extension. Covers identity, testing, and common pitfalls."
permalink: /articles/stripe-in-extensions/
---

Stripe in Extensions

Why Stripe matters for Chrome extension developers

When Google deprecated Chrome Web Store payments in 2020, many extension developers were left searching for alternatives. The Chrome Web Store had its problems, but it handled payments natively which meant one less thing to build. Since that deprecation, Stripe has become the dominant choice for extension monetization, and for good reason. The migration away from Google's solution forced the community to find something better, and Stripe stepped up.

Stripe gives you complete control over the entire payment experience. You decide when to show upgrade prompts, how to handle trial periods, and what happens when a payment fails. PayPal exists but feels clunky for consumer extensions. Paddle handles tax compliance but adds margin to your prices. Stripe is developer-friendly, well-documented, and integrates with everything. Most importantly, Stripe Checkout means you never touch raw credit card data, which simplifies PCI compliance significantly. The documentation is thorough, the API is stable, and the support team actually understands developer needs.

The basic payment flow

The payment flow for a Chrome extension using Stripe follows a clear sequence. When a user clicks an upgrade button in your extension popup or options page, your extension opens a Stripe Checkout session URL in a new browser tab. This is a hosted payment page provided by Stripe, so users see a professional interface they trust.

The user enters their payment information on Stripe's page and completes the purchase. Stripe then processes the payment and fires a webhook to your backend server with the payment details. Your server verifies the webhook signature to ensure it actually came from Stripe, extracts the customer information, and updates the user's subscription status in your database.

When the user interacts with your extension next, it either polls your server for the current subscription status or reads from a local cache. Based on that status, the extension either shows premium features or prompts for upgrade. This entire flow happens without your extension ever handling sensitive payment data.

Setting up Stripe Checkout

The Stripe Dashboard is where you configure products and prices. Create a product for each tier you offer, then create prices attached to that product. For subscriptions, create a recurring price with your chosen interval, whether monthly, yearly, or something else. For lifetime deals, create a one-time price that only charges once.

Use price IDs in your code rather than hardcoding dollar amounts. This separation lets you run promotions or adjust pricing without pushing code changes. Stripe price IDs look like price_abc123 and are stable identifiers you can safely reference.

Generating Checkout Session URLs happens server-side using the Stripe SDK. You create a session with the price ID, set success and cancel URLs, and optionally pass the user's email if you know it. The session URL gets sent back to your extension, which opens it in a browser tab. Stripe handles the entire payment page, so your server never sees card numbers.

One useful feature is passing metadata to the checkout session. Include your internal user ID, the extension version, or any context that helps reconcile payments later. This metadata comes back in webhooks and simplifies matching Stripe transactions to your user records.

## Stripe Checkout vs Payment Links vs Elements

Stripe offers three primary integration options for accepting payments, and choosing the right one depends on your extension's requirements and user experience goals.

**Stripe Checkout** is the hosted payment page you redirect users to. It handles the entire payment form, mobile optimization, error handling, and even optional tax calculation. For Chrome extensions, this is typically the best choice because users complete payment in a separate browser tab, avoiding complex iframe restrictions and content security policy issues. Checkout supports one-time purchases, subscriptions, and even promotional codes. The tradeoff is that users leave your extension's context to complete payment, which can reduce conversion slightly.

**Stripe Payment Links** are pre-built checkout pages you can share via URL. Unlike Checkout sessions which you generate programmatically, Payment Links are created in the Stripe Dashboard and provide a shareable link. These work well for simple one-time purchases where you want minimal code. However, they lack the ability to pass dynamic metadata or customize the experience based on the user's context. For extensions with evolving pricing or custom flows, Payment Links are limiting.

**Stripe Elements** provides the building blocks to embed payment forms directly in your website. This gives maximum control over the user experience but requires more development effort. Elements works well if you have an existing website where users already authenticate and manage accounts. However, embedding in extension popups or options pages can run afoul of Chrome's Content Security Policy restrictions. Elements inside an iframe inside an extension often creates cross-origin complications.

For most Chrome extension developers, Stripe Checkout remains the recommended choice. The hosted page approach works reliably across browsers, handles security concerns professionally, and requires minimal integration code. The key implementation detail is opening the Checkout URL in a new browser tab using the standard `window.open()` method from your extension's popup or background script, rather than trying to load it in an iframe.

Your backend generates the Checkout Session URL and returns it to your extension. The extension then calls `chrome.tabs.create({ url: sessionUrl })` to open the payment page. This approach avoids CSP issues entirely and provides a clean separation between your extension and the payment flow.

Use Payment Links when you have a static pricing page on your website and want to redirect users there from your extension. This works for simple lifetime deals or single-product offerings. Use Elements when you're building a full web application with integrated payments and have the engineering resources to handle the complexity.

Connecting the extension to Stripe identity

Matching users between your extension and Stripe requires choosing an identity approach. There are three common patterns, each with tradeoffs.

The first approach uses the Chrome identity API to get the user's Google email. This works well if your extension already requires the identity permission. You extract the email, look up the corresponding Stripe customer, and grant access. The limitation is that users must have a Google account, and you're tied to their Google identity.

The second approach builds a custom account system with email and password. Users create an account on your website, and you link that account to a Stripe customer ID. This gives you more flexibility but requires maintaining user accounts, password resets, and authentication. It's more work but works across browsers and platforms.

The third approach uses license keys with no account required. After payment, Stripe webhook delivers a license key. Users enter that key in your extension, and you validate it against your database. This is simple to implement but lacks recurring revenue capabilities since you cannot easily identify returning customers for renewals.

Most extension developers start with the Chrome identity approach because it requires the least infrastructure. However, if your extension becomes popular, you'll eventually want custom accounts. Plan for this from the start by storing a unique user identifier that doesn't depend on Google. This makes future migration easier.

Webhook handling

Webhooks are the backbone of your payment system. Your server receives events from Stripe and updates accordingly. There are four events you must handle.

Checkout.session.completed fires when any payment succeeds, whether initial subscription or one-time purchase. Extract the customer email, customer ID, and any metadata you attached. Create or update the user record in your database with the subscription status.

Customer.subscription.updated fires when a subscription changes. This happens when someone upgrades, downgrades, or changes their payment method. Update the subscription period dates and tier in your database.

Customer.subscription.deleted fires when a subscription cancels, either from user action or failed payment retries. Mark the user as no longer active and optionally grant a grace period before locking features.

Invoice.payment_failed fires when a recurring charge fails. This is critical for handling churn. You might email the user, add a warning in your extension, or immediately restrict access depending on your business rules. Stripe retries failed payments automatically three times over several days before giving up. Plan your grace period around this timeline.

Always verify webhook signatures. Stripe provides a signature in the header that you verify using your webhook secret. This prevents attackers from sending fake webhook events to grant free access.

## Webhook Security for Extensions

Securing your webhook endpoint is critical because it directly controls user access to your premium features. Without proper verification, attackers could send fake webhook events pretending to be from Stripe, granting themselves free subscriptions.

Stripe signatures use HMAC-SHA256. When Stripe sends a webhook, it includes a `Stripe-Signature` header containing a signed hash of the request body. Your server must reconstruct this signature using your webhook secret and compare it to the header value. If they match, the request is genuine.

The verification process requires extracting the timestamp and signature from the header, computing the expected signature using `HMAC-SHA256(timestamp + "." + payload, webhook_secret)`, and comparing signatures using a timing-safe comparison function to prevent timing attacks. Most Stripe SDKs provide built-in methods that handle this correctly.

Beyond signature verification, implement additional security measures. Validate that the webhook originates from Stripe's IP addresses, which you can find in Stripe's documentation. Add rate limiting to your webhook endpoint to prevent denial-of-service attacks. Log all webhook events for auditing, including failed verification attempts.

Handle duplicate events gracefully. Stripe may send the same webhook multiple times if it doesn't receive a 200 response. Your database operations should be idempotent—processing the same event twice shouldn't grant duplicate access or cause errors. Use the event ID to track processed events and skip duplicates.

For extensions, consider where your webhook endpoint runs. A serverless function (AWS Lambda, Vercel, Cloudflare Workers) works well for handling webhooks without maintaining a persistent server. The key is ensuring your function can reach your database to update user status. The extension's connection to Stripe is indirect—Stripe calls your server, your server updates the database, and the extension reads from there.

Implement a webhook signature verification library in your backend. Here's the essential pattern using Node.js:

```
const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);

app.post('/webhook', express.raw({ type: 'application/json' }), (req, res) => {
  const sig = req.headers['stripe-signature'];
  let event;
  try {
    event = stripe.webhooks.constructEvent(req.body, sig, process.env.STRIPE_WEBHOOK_SECRET);
  } catch (err) {
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }
  // Handle the event
  switch (event.type) { /* ... */ }
  res.json({ received: true });
});
```

Always use environment variables for your webhook secret, never hardcode it in your codebase. Rotate secrets periodically and immediately revoke any that are compromised.

Test your webhook security by attempting to send fake events. Use Stripe CLI to replay webhooks and verify your handler processes them correctly. Regularly audit your webhook logs for suspicious patterns like repeated failed verifications or unexpected event types.

Testing the full flow

Stripe test mode lets you simulate payments without real money. Use test card numbers like 4242424242424242 for successful charges. For specific failure scenarios, Stripe provides test cards that decline for various reasons.

Test successful payments end-to-end. Click the upgrade button, complete the payment, verify the webhook fires, check your database updates, and confirm the extension unlocks.

Test failed payments. Use a card that declines or has insufficient funds. Verify your extension handles this gracefully. Do users see a clear error message, or does nothing happen?

Test cancellation flow. Cancel a test subscription and verify the webhook fires. Check that your extension properly reverts to free tier after the subscription period ends.

Test server-down scenarios. What happens when your API is unreachable? Some extensions fail closed and lock users out immediately. Others fail open and grant temporary access. Consider a grace period where users can still use premium features while your server recovers.

Also test the timing between payment and webhook delivery. Stripe webhooks typically arrive within seconds but can occasionally be delayed. If your extension checks status immediately after payment succeeds, you might get a false negative. Build in a retry mechanism or show a "payment processing" state rather than immediately locking features.

Common pitfalls

Caching subscription status locally is essential. Calling your server on every extension action creates latency and rate limiting problems. Cache the status with a TTL between one and six hours depending on how critical real-time accuracy is. When the cache expires, fetch fresh status on next user interaction.

Stripe Customer Portal saves you support emails. Enable it in the Stripe Dashboard and link to it from your extension. Users can update payment methods, cancel subscriptions, and download invoices without contacting you. This self-service capability is expected in 2024. The portal URL is specific to each customer, so generate it dynamically when the user requests it, passing their email or customer ID.

Currency and tax compliance matters. If you sell globally, you need to handle VAT, GST, and sales tax. Stripe Tax automates this based on customer location. Enable it in the Dashboard and configure your product prices to include or exclude tax as needed. This adds complexity to your pricing but keeps you compliant with international regulations.

Cross-device access trips up many implementations. A user might pay on their laptop but primarily use your extension on their desktop. Your database must link the Stripe customer to the user identity, not to a specific device. Sync status across all devices when the user authenticates. If using the Chrome identity approach, the email serves as the common identifier across devices.

Handling subscription cancellations from the Stripe dashboard directly is another edge case. Some users cancel through the Stripe Customer Portal rather than through your extension. Your customer.subscription.deleted webhook still fires, but you might want to send a follow-up email thanking them and offering a discount to return.

Tracking the subscription period matters for user experience. Store both the subscription start date and the current period end date. Show users when their subscription renews or expires. This transparency builds trust and reduces support questions about billing timing.

The Zovo Pro payment flow

The Zovo Pro monetization system at zovo.one demonstrates this pattern in production. We handle both subscriptions at $4.99 per month and lifetime deals at $99, across 17 different Chrome extensions, using a single Stripe integration.

Our backend receives webhooks from Stripe and updates a shared customer database. When any user upgrades, they get access to all our extensions through a unified account system. The same webhook processing code works regardless of which extension triggered the purchase.

This shared infrastructure approach means we maintain one payment flow instead of 17 separate ones. When Stripe releases new features or changes pricing, we update one integration. This has been running for years with minimal maintenance.

One thing we learned the hard way is handling plan changes. When switching from monthly to yearly, or adding new features, the subscription.updated webhook fires but the existing period might not reflect immediate changes. We implemented a feature flag system in our database that toggles independently of the subscription period. This way, new features roll out immediately while the old subscription continues until renewal.

If you're building monetization into a Chrome extension, Stripe Checkout combined with webhook processing and a simple status check is the proven path. It scales from a single extension to dozens, handles the complexity of subscriptions and renewals, and lets you focus on building your extension instead of payment infrastructure.

Starting simple is smart. Get the basic flow working first, then add features like trial periods, coupon codes, and subscription management later. The foundation matters more than the bells and whistles.

## Step-by-Step Stripe Integration with Chrome Extensions

The integration process involves several distinct phases that work together to create a seamless payment experience. This section walks through each phase in detail, from initial setup to the final production deployment.

**Phase 1: Stripe Account and Product Setup**

Before writing any code, set up your Stripe account and create the products users will purchase. In the Stripe Dashboard, navigate to the Products section and create a new product for each subscription tier you want to offer. For a typical Chrome extension, you might create a "Pro" tier at $4.99/month and a "Lifetime" tier as a one-time purchase.

When creating prices, use the Stripe API or Dashboard to generate price IDs. These IDs are stable identifiers that look like `price_1PxyzABC123` and allow you to change pricing without code updates. Store these price IDs in your extension's configuration or fetch them from your backend.

**Phase 2: Backend Server Configuration**

Your extension needs a backend server to communicate with Stripe securely. This server handles creating checkout sessions, verifying webhook signatures, and managing user subscription data. The server can be a Node.js Express app, a Python Flask service, or a serverless function.

Set up environment variables for your Stripe keys: `STRIPE_SECRET_KEY` for server-side operations and `STRIPE_PUBLISHABLE_KEY` for client-side code. Never expose the secret key in your extension—always proxy through your backend.

**Phase 3: Extension Manifest and Permissions**

Update your extension's `manifest.json` to include necessary permissions. You'll need at minimum the `storage` permission for caching subscription status and optionally `identity` for retrieving the user's Google email.

```json
{
  "permissions": [
    "storage",
    "identity"
  ],
  "host_permissions": [
    "https://your-backend-server.com/*"
  ]
}
```

**Phase 4: Opening Stripe Checkout from Extension**

When a user clicks an upgrade button, your extension calls your backend to generate a checkout session URL, then opens that URL in a new tab. Never try to embed Stripe Checkout in an iframe—Chrome's Content Security Policy blocks this, and it creates poor user experience anyway.

## Code Example: Background Script Payment Flow

The background script (or service worker in Manifest V3) orchestrates the payment flow. Here's a complete implementation pattern:

```javascript
// background.js (Manifest V3 Service Worker)

// Listen for upgrade button clicks from popup or options page
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'INITIATE_UPGRADE') {
    handleUpgrade(message.tier, message.priceId)
      .then(result => sendResponse(result))
      .catch(error => sendResponse({ error: error.message }));
    return true; // Keep channel open for async response
  }
});

async function handleUpgrade(tier, priceId) {
  try {
    // Call your backend to create a checkout session
    const response = await fetch('https://your-api.com/create-checkout-session', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        // Include authentication headers if needed
      },
      body: JSON.stringify({
        priceId: priceId,
        userId: await getUserId(), // Get from storage or identity
        extensionVersion: chrome.runtime.getManifest().version,
      })
    });

    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }

    const { sessionUrl } = await response.json();

    // Open Stripe Checkout in a new tab
    await chrome.tabs.create({ url: sessionUrl });

    return { success: true, message: 'Opening payment page...' };
  } catch (error) {
    console.error('Upgrade failed:', error);
    return { success: false, error: error.message };
  }
}

async function getUserId() {
  // Try to get user ID from storage, or use identity API
  return new Promise((resolve) => {
    chrome.storage.local.get(['userId'], (result) => {
      resolve(result.userId || null);
    });
  });
}

// Poll for subscription status after payment completes
async function pollSubscriptionStatus(userId, maxAttempts = 10) {
  for (let i = 0; i < maxAttempts; i++) {
    await sleep(2000); // Wait 2 seconds between checks
    
    const response = await fetch(`https://your-api.com/subscription-status?userId=${userId}`);
    const data = await response.json();
    
    if (data.status === 'active') {
      // Update local cache
      await chrome.storage.local.set({
        subscriptionStatus: 'premium',
        subscriptionTier: data.tier,
        periodEnd: data.periodEnd
      });
      return data;
    }
  }
  
  throw new Error('Payment verification timed out');
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
```

This background script handles the complete payment initiation flow. It receives messages from your popup or options page, calls your backend securely, opens the Stripe Checkout URL, and can optionally poll for payment confirmation.

## Code Example: Content Script Triggers

Content scripts run in the context of web pages and can trigger upgrade prompts based on user behavior. Here's how to implement contextual upgrade triggers:

```javascript
// content.js - Triggering upgrade prompts based on page context

// Listen for messages from the background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'SHOW_UPGRADE_PROMPT') {
    showUpgradeModal(message.feature, message.limit);
  }
});

// Example: Detect when user hits a usage limit
function checkUsageLimits() {
  const usage = getCurrentUsage(); // Your usage tracking logic
  
  const limits = {
    free: 10,
    pro: 100
  };
  
  if (usage.requests >= limits.free && !window.isPremiumUser) {
    // Notify background script to show upgrade prompt
    chrome.runtime.sendMessage({
      type: 'TRIGGER_UPGRADE',
      context: {
        feature: 'API Requests',
        current: usage.requests,
        limit: limits.free,
        upgradeBenefit: `Upgrade to Pro for ${limits.pro} requests/month`
      }
    });
  }
}

// Show an inline upgrade prompt (be careful with page injection)
function showUpgradeModal(feature, limit) {
  // Create modal DOM elements
  const modal = document.createElement('div');
  modal.className = 'extension-upgrade-modal';
  modal.innerHTML = `
    <div class="modal-content">
      <h3>Upgrade to Pro</h3>
      <p>You've reached your ${feature} limit (${limit} free).</p>
      <p>Upgrade now to unlock unlimited access!</p>
      <button id="upgrade-btn">Upgrade Now</button>
      <button id="dismiss-btn">Maybe Later</button>
    </div>
  `;
  
  // Inject styles
  const style = document.createElement('style');
  style.textContent = `
    .extension-upgrade-modal {
      position: fixed; top: 0; left: 0; right: 0; bottom: 0;
      background: rgba(0,0,0,0.5); z-index: 999999;
      display: flex; align-items: center; justify-content: center;
    }
    .modal-content {
      background: white; padding: 24px; border-radius: 8px;
      text-align: center; max-width: 400px;
    }
    #upgrade-btn {
      background: #635bff; color: white; border: none;
      padding: 12px 24px; border-radius: 4px; cursor: pointer;
      font-size: 16px; margin: 8px;
    }
    #dismiss-btn {
      background: #f0f0f0; border: none;
      padding: 12px 24px; border-radius: 4px; cursor: pointer;
      margin: 8px;
    }
  `;
  document.head.appendChild(style);
  document.body.appendChild(modal);
  
  // Handle button clicks
  document.getElementById('upgrade-btn').addEventListener('click', () => {
    modal.remove();
    chrome.runtime.sendMessage({ type: 'INITIATE_UPGRADE', tier: 'pro' });
  });
  
  document.getElementById('dismiss-btn').addEventListener('click', () => {
    modal.remove();
  });
}

// Run usage checks periodically
setInterval(checkUsageLimits, 30000);
```

This content script monitors usage and triggers upgrade prompts when users hit free tier limits. The key is providing contextual, non-intrusive prompts that appear when users are most likely to convert.

## Webhook Handling for Subscription Management

Webhooks are the authoritative source of truth for subscription status. When Stripe processes a payment or subscription change, it sends an HTTP POST to your server with event details. Your webhook handler processes these events and updates your database accordingly.

### Essential Webhook Events to Handle

```javascript
// webhook-handler.js - Complete webhook processing

const stripe = require('stripe')(process.env.STRIPE_SECRET_KEY);
const express = require('express');
const app = express();

// Use express.raw() for Stripe webhooks - signature verification requires raw body
app.post('/webhooks/stripe', express.raw({ type: 'application/json' }), async (req, res) => {
  const sig = req.headers['stripe-signature'];
  let event;
  
  // Verify the webhook signature
  try {
    event = stripe.webhooks.constructEvent(
      req.body, 
      sig, 
      process.env.STRIPE_WEBHOOK_SECRET
    );
  } catch (err) {
    console.error(`Webhook signature verification failed: ${err.message}`);
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }
  
  // Handle the event
  try {
    await handleStripeEvent(event);
  } catch (err) {
    console.error('Error handling event:', err);
    // Still return 200 to prevent Stripe from retrying
  }
  
  res.json({ received: true });
});

async function handleStripeEvent(event) {
  switch (event.type) {
    
    // ==========================================
    // CHECKOUT SESSION COMPLETED
    // ==========================================
    case 'checkout.session.completed': {
      const session = event.data.object;
      
      // Extract customer information
      const customerId = session.customer;
      const customerEmail = session.customer_email;
      const priceId = session.price?.id;
      const metadata = session.metadata || {};
      
      // Determine purchase type from price
      const isSubscription = session.subscription !== null;
      
      if (isSubscription) {
        // Get subscription details
        const subscription = await stripe.subscriptions.retrieve(session.subscription);
        
        await updateUserSubscription({
          stripeCustomerId: customerId,
          email: customerEmail,
          status: subscription.status,
          priceId: priceId,
          currentPeriodStart: new Date(subscription.current_period_start * 1000),
          currentPeriodEnd: new Date(subscription.current_period_end * 1000),
          subscriptionId: subscription.id,
          metadata: metadata
        });
      } else {
        // One-time purchase (lifetime license)
        await grantLifetimeAccess({
          stripeCustomerId: customerId,
          email: customerEmail,
          priceId: priceId,
          metadata: metadata
        });
      }
      break;
    }
    
    // ==========================================
    // SUBSCRIPTION UPDATED
    // ==========================================
    case 'customer.subscription.updated': {
      const subscription = event.data.object;
      
      await updateSubscriptionDetails({
        subscriptionId: subscription.id,
        stripeCustomerId: subscription.customer,
        status: subscription.status,
        priceId: subscription.items.data[0]?.price?.id,
        currentPeriodStart: new Date(subscription.current_period_start * 1000),
        currentPeriodEnd: new Date(subscription.current_period_end * 1000),
        cancelAtPeriodEnd: subscription.cancel_at_period_end
      });
      break;
    }
    
    // ==========================================
    // SUBSCRIPTION DELETED (Canceled)
    // ==========================================
    case 'customer.subscription.deleted': {
      const subscription = event.data.object;
      
      await revokeSubscription({
        subscriptionId: subscription.id,
        stripeCustomerId: subscription.customer,
        reason: 'subscription_cancelled'
      });
      break;
    }
    
    // ==========================================
    // INVOICE PAYMENT FAILED
    // ==========================================
    case 'invoice.payment_failed': {
      const invoice = event.data.object;
      
      await handleFailedPayment({
        stripeCustomerId: invoice.customer,
        subscriptionId: invoice.subscription,
        amountDue: invoice.amount_due,
        nextPaymentAttempt: invoice.next_payment_attempt,
        invoiceId: invoice.id
      });
      break;
    }
    
    // ==========================================
    // INVOICE PAYMENT SUCCEEDED
    // ==========================================
    case 'invoice.payment_succeeded': {
      const invoice = event.data.object;
      
      await confirmPaymentReceived({
        stripeCustomerId: invoice.customer,
        subscriptionId: invoice.subscription,
        amountPaid: invoice.amount_paid,
        invoiceId: invoice.id
      });
      break;
    }
    
    // ==========================================
    // CUSTOMER CREATED
    // ==========================================
    case 'customer.created': {
      const customer = event.data.object;
      
      // Optionally create a user record when first customer is created
      await createUserRecord({
        stripeCustomerId: customer.id,
        email: customer.email
      });
      break;
    }
  }
}

// Database helper functions (implement according to your stack)
async function updateUserSubscription(data) {
  // Update your user database with subscription info
  console.log('Updating subscription for:', data.email);
  // Implementation depends on your database (PostgreSQL, MongoDB, etc.)
}

async function grantLifetimeAccess(data) {
  // Grant lifetime access for one-time purchases
  console.log('Granting lifetime access for:', data.email);
}

async function updateSubscriptionDetails(data) {
  // Update existing subscription details
  console.log('Updating subscription:', data.subscriptionId);
}

async function revokeSubscription(data) {
  // Revoke access when subscription is cancelled
  console.log('Revoking subscription for customer:', data.stripeCustomerId);
}

async function handleFailedPayment(data) {
  // Send notification to user about failed payment
  console.log('Payment failed for customer:', data.stripeCustomerId);
  
  // Optionally send email notification
  await sendEmailNotification({
    to: data.email,
    subject: 'Payment Failed - Action Required',
    body: 'Your payment could not be processed. Please update your payment method.'
  });
}
```

### Subscription Status States

Stripe subscriptions can be in several states. Understanding these states helps you implement proper access control:

- **active**: Subscription is current and payments are processing. User has full access.
- **trialing**: User is in a free trial period. Full access granted.
- **past_due**: Payment failed but Stripe is retrying. User typically retains access during retry period.
- **canceled**: Subscription ended (either user canceled or payment failed permanently). No access.
- **unpaid**: Similar to past_due but requires manual intervention.
- **paused**: User paused their subscription (if enabled in Stripe).

Map these states to your extension's feature access appropriately. Most implementations treat `active` and `trialing` as "has access," while other states trigger access restrictions.

## Testing Payments in Development

Testing payment flows requires a deliberate approach that covers both success and failure scenarios. Stripe provides robust testing tools that simulate various payment situations without real money changing hands.

### Setting Up Test Mode

In the Stripe Dashboard, toggle between "Live" and "Test" mode using the switch in the top-right corner. Generate test API keys and add them to your backend environment:

```
STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

Install the Stripe CLI to forward webhooks to your local development server:

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Log in to your Stripe account
stripe login

# Forward webhooks to localhost
stripe listen --forward-to localhost:3000/webhooks/stripe
```

The CLI provides a webhook secret for local testing. Use this secret in your local environment to verify webhook signatures.

### Test Card Numbers

Stripe provides specific test card numbers for different scenarios:

| Card Number | Scenario |
|------------|----------|
| 4242424242424242 | Successful payment |
| 4000002500003155 | Requires authentication |
| 4000000000000002 | Card declined |
| 4000000000009995 | Insufficient funds |
| 4000000000000069 | Expired card |
| 4000000000000127 | Processing error |

Use these cards to test the complete user flow. For subscriptions, the card is charged repeatedly, so use the successful card for ongoing subscription tests.

### End-to-End Testing Checklist

Test each scenario in your payment flow systematically:

1. **Successful one-time purchase**: Complete a purchase with the test card 4242424242424242. Verify webhook fires, database updates, and extension unlocks.

2. **Failed payment**: Use card 4000000000000002. Verify graceful error handling with clear user messaging.

3. **Subscription creation and renewal**: Create a subscription with the test card. Verify the customer.subscription.created webhook processes correctly.

4. **Subscription cancellation**: Cancel through both your extension UI and the Stripe Customer Portal. Verify customer.subscription.deleted webhook processes.

5. **Payment method update**: Use the Stripe testing flow to update a payment method. Verify the extension handles the change.

6. **Trial period conversion**: If offering trials, test the transition from trial to active billing.

7. **Refund processing**: Process a test refund and verify the extension correctly restricts access.

8. **Cross-device sync**: Test on multiple devices/browsers to ensure subscription status syncs correctly.

### Testing the Extension Flow

Create a dedicated test user flow in your extension that bypasses payment for development:

```javascript
// Development-only helper
function enableDevMode(userId) {
  if (chrome.runtime.id === 'EXTENSION_ID_FOR_DEV') { // Only in dev
    chrome.storage.local.set({
      subscriptionStatus: 'premium',
      subscriptionTier: 'pro',
      periodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      _devMode: true
    });
  }
}
```

Disable this in production using environment checks or build-time configuration.

## PCI Compliance Considerations

One of Stripe's primary benefits is reducing your PCI compliance burden. Since users enter card details on Stripe's hosted pages rather than your extension, you avoid handling raw card data directly. However, understanding compliance requirements helps you build a more secure system.

### What PCI Compliance Means for Extension Developers

The Payment Card Industry Data Security Standard (PCI DSS) is a set of security requirements for any entity that stores, processes, or transmits cardholder data. The standard has four levels based on transaction volume, with most extension developers falling under Level 4 (fewer than 20,000 transactions annually).

When using Stripe Checkout, you don't store, process, or transmit cardholder data—Stripe handles all of that. This means you fall under the simplest compliance requirements: SAQ-A (Self-Assessment Questionnaire A).

SAQ-A requirements are minimal because you outsource payment processing to a PCI-compliant provider. You confirm compliance by:

1. Using Stripe Checkout (hosted payment page) exclusively
2. Not storing cardholder data on your servers
3. Ensuring your extension doesn't intercept or log payment information
4. Maintaining basic security practices for your website and extension

### Implementation Best Practices

Even with Stripe handling the sensitive data, follow these security practices:

**Never log payment information**: Ensure your server logs, extension console logs, and error tracking systems never capture card numbers, CVV, or payment amounts in plain text.

```javascript
// ❌ Never do this
console.log('Payment received:', paymentDetails.cardNumber);

// ✅ Safe logging
console.log('Payment received for customer:', customerId, 'amount:', amount);
```

**Use HTTPS everywhere**: Your backend, any websites you control, and all API endpoints must use HTTPS. Chrome and modern browsers will block payment flows from HTTP.

**Secure your webhook endpoint**: Implement signature verification as shown in the webhook section. This prevents attackers from sending fake payment confirmation events.

**Store only what you need**: Keep customer IDs and subscription status, but avoid storing billing addresses, phone numbers, or other PII unless necessary.

### What Happens If There's a Data Breach

If your systems are compromised and you do store card data, you face significant consequences: forensic audits, potential fines from card networks, legal liability, and severe reputational damage. Using Stripe Checkout eliminates this risk because card data never touches your systems.

Stripe is PCI Level 1 certified—the highest level of compliance. Their infrastructure undergoes regular audits and penetration testing. You're essentially inheriting their compliance by using their hosted payment pages.

## Handling Failed Payments and Dunning

Failed payments are inevitable in any subscription business. Whether cards expire, are lost, or customers have insufficient funds, you need a strategy for handling these situations gracefully. This process is called "dunning"—the practice of communicating with customers to ensure payment collection.

### Understanding Stripe's Automatic Retry Logic

When a recurring payment fails, Stripe automatically retries the charge according to its schedule:

| Attempt | Timing |
|---------|--------|
| 1 | Immediately |
| 2 | 3 days after first failure |
| 3 | 5 days after second attempt |

After three failed attempts (roughly 12 days from initial failure), Stripe marks the subscription as canceled and fires the `customer.subscription.deleted` webhook.

This automatic retry gives you time to notify users and attempt recovery before losing the customer entirely.

### Implementing Dunning Notifications

Send proactive notifications when payments fail:

```javascript
async function handleFailedPayment(data) {
  const { stripeCustomerId, subscriptionId, nextPaymentAttempt } = data;
  
  // Get customer email from your database
  const customer = await getCustomerByStripeId(stripeCustomerId);
  
  // Send first failure notification
  if (nextPaymentAttempt) {
    await sendEmail({
      to: customer.email,
      subject: 'Payment failed - We\'ll try again',
      template: 'payment-failed-first',
      data: {
        retryDate: new Date(nextPaymentAttempt * 1000).toLocaleDateString(),
        amount: data.amountDue / 100
      }
    });
    
    // Also update extension if user is currently using it
    await notifyExtensionUser(customer.id, {
      type: 'payment_warning',
      message: 'Payment issue detected. Please update your payment method.'
    });
  }
  
  // Log for analytics
  await logDunningEvent({
    customerId: customer.id,
    subscriptionId: subscriptionId,
    attempt: data.attemptCount || 1,
    event: 'payment_failed'
  });
}
```

### Grace Period Implementation

Provide a grace period after payment failures before restricting access:

```javascript
function calculateAccessStatus(subscription, failedPaymentDate) {
  const now = new Date();
  
  if (subscription.status === 'active') {
    return { hasAccess: true, reason: 'active_subscription' };
  }
  
  if (subscription.status === 'past_due' && failedPaymentDate) {
    const daysSinceFailure = Math.floor(
      (now - new Date(failedPaymentDate)) / (1000 * 60 * 60 * 24)
    );
    
    // 7-day grace period
    if (daysSinceFailure <= 7) {
      return { 
        hasAccess: true, 
        reason: 'grace_period',
        daysRemaining: 7 - daysSinceFailure
      };
    }
  }
  
  return { hasAccess: false, reason: 'payment_required' };
}
```

### Customer Portal Integration

Enable the Stripe Customer Portal so users can update payment methods themselves:

```javascript
// Backend: Create customer portal session
app.post('/create-portal-session', async (req, res) => {
  const { customerId } = req.body;
  
  const session = await stripe.billingPortal.sessions.create({
    customer: customerId,
    return_url: `${process.env.APP_URL}/settings`
  });
  
  res.json({ url: session.url });
});
```

The Customer Portal allows users to:
- Update payment methods
- Download invoices
- Cancel subscriptions
- View billing history
- Change subscription tiers

Include a link to the portal in your extension's settings or account page. This self-service capability significantly reduces support burden.

### Recovering Lost Customers

For subscriptions that were canceled due to payment failure, consider recovery campaigns:

1. **Win-back emails**: Send a series of emails offering a discount to resubscribe
2. **In-extension reminders**: Show a subtle prompt encouraging users to update payment and resubscribe
3. **Special offers**: Offer a month free or a discounted rate for returning customers

Track these metrics:
- Payment failure rate (target: below 5%)
- Recovery rate (subscriptions saved through dunning)
- Time to recover (how quickly users update payment after notification)

## Related Implementation Guides

- [Server-Side Validation](/articles/server-side-validation/) — Securing your extension's backend payment validation
- [License Key System](/articles/license-key-system/) — Implementing license keys for one-time purchases
- [Subscription Model](/articles/subscription-model/) — Managing recurring revenue with Stripe
- [One-Time Purchase](/articles/one-time-purchase/) — Selling lifetime licenses and single purchases

---

## Technical Implementation

For the code behind these strategies, see the companion [Chrome Extension Guide](https://github.com/theluckystrike/chrome-extension-guide):

- [Background Service Workers](https://github.com/theluckystrike/chrome-extension-guide/blob/main/docs/mv3/service-workers.md) — Handling payment callbacks and background tasks in MV3
- [Fetch API Patterns](https://github.com/theluckystrike/chrome-extension-guide/blob/main/docs/patterns/fetch-patterns.md) — Making server requests from extensions securely
- [Authentication Patterns](https://github.com/theluckystrike/chrome-extension-guide/blob/main/docs/patterns/authentication-patterns.md)
- [Content Security Policy](https://github.com/theluckystrike/chrome-extension-guide/blob/main/docs/mv3/content-security-policy.md)

All tools and guides are part of the [Zovo](https://zovo.one) ecosystem.

---

## Related Articles

- [Chrome Web Store Payments](articles/chrome-web-store-payments.md)
- [Server Side Validation](articles/server-side-validation.md)
- [Subscription Model](articles/subscription-model.md)


---

Part of the Extension Monetization Playbook by theluckystrike. Professional Chrome extension development at zovo.one
