---

layout: default
title: "Stripe Integration for Chrome Extensions"
description: "Integrate Stripe payments into your Chrome extension. Subscriptions, one-time payments, and trials."
permalink: /payments/stripe-in-extensions/

---


# Stripe Payment Integration for Chrome Extensions

When Google deprecated Chrome Web Store payments in 2020, many extension developers were left searching for alternatives. The Chrome Web Store had its problems, but it handled payments natively which meant one less thing to build. Since that deprecation, Stripe has become the dominant choice for extension monetization, and for good reason. The migration away from Google's solution forced the community to find something better, and Stripe stepped up.

Stripe gives you complete control over the entire payment experience. You decide when to show upgrade prompts, how to handle trial periods, and what happens when a payment fails. PayPal exists but feels clunky for consumer extensions. Paddle handles tax compliance but adds margin to your prices. Stripe is developer-friendly, well-documented, and integrates with everything. Most importantly, Stripe Checkout means you never touch raw credit card data, which simplifies PCI compliance significantly. The documentation is thorough, the API is stable, and the support team actually understands developer needs.

The basic payment flow

The payment flow for a Chrome extension using Stripe follows a clear sequence. When a user clicks an upgrade button in your extension popup or options page, your extension opens a Stripe Checkout session URL in a new browser tab. This is a hosted payment page provided by Stripe, so users see a professional interface they trust.

The user enters their payment information on Stripe's page and completes the purchase. Stripe then processes the payment and fires a webhook to your backend server with the payment details. Your server verifies the webhook signature to ensure it actually came from Stripe, extracts the customer information, and updates the user's subscription status in your database.

When the user interacts with your extension next, it either polls your server for the current subscription status or reads from a local cache. Based on that status, the extension either shows premium features or prompts for upgrade. This entire flow happens without your extension ever handling sensitive payment data.

## Payment Processor Comparison for Chrome Extensions

Choosing the right payment processor is crucial for your extension's success. Here's how Stripe compares to other popular options for extension monetization:

| Feature | Stripe | ExtensionPay | Paddle | Gumroad |
|---------|--------|--------------|--------|---------|
| **Developer Experience** | Excellent | Good | Good | Good |
| **Extension-Specific Support** | Via community | Yes | No | No |
| **PCI Compliance** | SAQ-A | SAQ-A | SAQ-A | SAQ-A |
| **Tax Handling** | Stripe Tax (extra cost) | Built-in | Built-in | Limited |
| **Platform Fee** | 2.9% + 30¢ | 5% + 50¢ | 5% + 50¢ | 10% |
| **Subscription Management** | Excellent | Good | Good | Basic |
| **Customer Portal** | Yes | Limited | Yes | Limited |
| **Webhook Reliability** | Excellent | Good | Good | Variable |
| **Test Mode** | Robust | Good | Good | Basic |
| **Multi-Currency** | 135+ currencies | Limited | 200+ | Limited |

**Why Stripe Wins for Extensions:**

1. **Developer-Friendly API**: Stripe's API is consistently well-documented and stable. The SDK works seamlessly with Node.js, Python, and other backend languages.

2. **Flexible Integration**: You have complete control over the payment flow. No iframe restrictions or forced branding.

3. **Webhook Reliability**: Stripe's webhook delivery is industry-leading with automatic retries and detailed event logs.

4. **Customer Portal**: Users can manage subscriptions, update payment methods, and download invoices without your support team.

5. **Extensible**: As your extension grows, Stripe scales with you—from simple one-time purchases to complex enterprise billing.

ExtensionPay (formerly Mac和应用) is popular in the Chinese market but lacks global support. Paddle handles VAT but adds significant margin. Gumroad is simple but designed for creators, not software products.

## Architecture Overview

Understanding the full payment flow is essential before writing code. Here's the complete architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STRIPE PAYMENT FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────────┐       ┌─────────────────┐       ┌──────────────────┐  │
│   │   Chrome     │       │   Your Backend  │       │    Stripe API    │  │
│   │  Extension   │       │      Server     │       │                  │  │
│   └──────┬───────┘       └────────┬────────┘       └────────┬─────────┘  │
│          │                        │                         │             │
│          │  1. User clicks        │                         │             │
│          │  "Upgrade" button     │                         │             │
│          ├──────────────────────>│                         │             │
│          │                        │                         │             │
│          │                        │  2. Create Checkout    │             │
│          │                        │     Session            │             │
│          │                        ├────────────────────────>│             │
│          │                        │                         │             │
│          │                        │  3. Return Session     │             │
│          │                        │     URL                │             │
│          │                        <────────────────────────┤             │
│          │                        │                         │             │
│          │  4. Open Checkout      │                         │             │
│          │     in new tab        │                         │             │
│          ├──────────────────────>│   (Browser Tab)         │             │
│          │                        │                         │             │
│          │                        │                         │             │
│          └────────────────────────┴─────────────────────────┴─────────────┘
│                                       │                                       │
│                                       │ 5. Payment processing                 │
│                                       │    (Stripe handles card data)        │
│                                       │                                       │
│                                       ▼                                       │
│                              ┌────────────────┐                             │
│                              │  User enters   │                             │
│                              │  payment info  │                             │
│                              └────────────────┘                             │
│                                       │                                       │
│                                       ▼                                       │
│   ┌──────────────┐       ┌─────────────────┐       ┌──────────────────┐  │
│   │   Chrome     │       │   Your Backend  │       │    Stripe API    │  │
│   │  Extension   │       │      Server     │       │                  │  │
│   └──────┬───────┘       └────────┬────────┘       └────────┬─────────┘  │
│          │                        ▲                         │             │
│          │                        │  6. Webhook event      │             │
│          │                        │     (checkout.session. │             │
│          │                        │      completed)         │             │
│          │                        │<────────────────────────┤             │
│          │                        │                         │             │
│          │                        │  7. Verify signature,  │             │
│          │                        │     update license in   │             │
│          │                        │     database            │             │
│          │                        │                         │             │
│          │  8. License check/     │                         │             │
│          │     sync on next use   │                         │             │
│          ├───────────────────────>│                         │             │
│          │                        │                         │             │
└──────────┴────────────────────────┴─────────────────────────┴─────────────┘
```

### Why You MUST Have a Backend Server

**Critical Security Requirement:** You cannot integrate Stripe directly in your Chrome extension because doing so would expose your Stripe secret key. Chrome extensions are client-side code that can be inspected, decompiled, and modified by anyone. Your secret key would be visible in the extension's source code, allowing attackers to process payments through your account.

The backend server acts as a secure intermediary:

1. **Secret Key Protection**: Your Stripe secret key (`sk_live_...`) never leaves your server
2. **Webhook Verification**: The server verifies that webhooks actually came from Stripe
3. **License Management**: The server maintains the authoritative record of who has paid
4. **API Rate Limiting**: Protects against abuse
5. **Business Logic**: Enforces your specific licensing rules and trial periods

Popular backend options include:
- **Express.js (Node.js)**: Most common, excellent Stripe SDK
- **FastAPI (Python)**: Great for Python developers
- **Serverless Functions**: Vercel, Cloudflare Workers, AWS Lambda
- **BaaS**: Firebase Cloud Functions, Supabase Edge Functions

This guide uses Node.js/Express, but the concepts apply to any backend.

## Setting up Stripe Checkout

The Stripe Dashboard is where you configure products and prices. Create a product for each tier you offer, then create prices attached to that product. For subscriptions, create a recurring price with your chosen interval, whether monthly, yearly, or something else. For lifetime deals, create a one-time price that only charges once.

Use price IDs in your code rather than hardcoding dollar amounts. This separation lets you run promotions or adjust pricing without pushing code changes. Stripe price IDs look like price_abc123 and are stable identifiers you can safely reference.

Generating Checkout Session URLs happens server-side using the Stripe SDK. You create a session with the price ID, set success and cancel URLs, and optionally pass the user's email if you know it. The session URL gets sent back to your extension, which opens it in a browser tab. Stripe handles the entire payment page, so your server never sees card numbers.

One useful feature is passing metadata to the checkout session. Include your internal user ID, the extension version, or any context that helps reconcile payments later. This metadata comes back in webhooks and simplifies matching Stripe transactions to your user records.

## Complete TypeScript Backend: server.ts

Here's a production-ready Express server with complete Stripe integration:

```typescript
// server.ts - Complete Express backend with Stripe integration
import express, { Request, Response, NextFunction } from 'express';
import Stripe from 'stripe';
import crypto from 'crypto';
import cors from 'cors';
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';

// Initialize Stripe with your secret key
const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-12-18.acacia',
});

const app = express();
const PORT = process.env.PORT || 3000;

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['chrome-extension://*'],
  methods: ['POST', 'GET'],
}));

// Rate limiting to prevent abuse
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: { error: 'Too many requests, please try again later' },
});
app.use('/api/', limiter);

// Webhook requires raw body, so we handle it separately
app.post('/webhooks/stripe', express.raw({ type: 'application/json' }), 
  handleStripeWebhook
);

// Body parsing for other routes
app.use(express.json());

// ==========================================
// TYPE DEFINITIONS
// ==========================================

interface User {
  id: string;
  email: string;
  stripeCustomerId?: string;
  subscriptionStatus: 'free' | 'active' | 'trialing' | 'past_due' | 'canceled';
  subscriptionTier?: string;
  subscriptionId?: string;
  periodStart?: Date;
  periodEnd?: Date;
  licenseKey?: string;
  createdAt: Date;
  updatedAt: Date;
}

interface CheckoutRequest {
  priceId: string;
  userId: string;
  email?: string;
  extensionVersion: string;
  trialDays?: number;
}

// ==========================================
// CHECKOUT SESSION CREATION
// ==========================================

app.post('/api/create-checkout-session', 
  limiter,
  async (req: Request, res: Response): Promise<void> => {
    try {
      const { priceId, userId, email, extensionVersion, trialDays } = req.body 
        as CheckoutRequest;

      if (!priceId || !userId) {
        res.status(400).json({ error: 'Missing required fields: priceId, userId' });
        return;
      }

      // Get or create Stripe customer
      let customerId = await getStripeCustomerId(userId, email);
      
      if (!customerId) {
        const customer = await stripe.customers.create({
          email,
          metadata: {
            userId,
            extensionVersion,
          },
        });
        customerId = customer.id;
        await linkUserToCustomer(userId, customerId);
      }

      // Determine if this is a subscription or one-time purchase
      const price = await stripe.prices.retrieve(priceId);
      const isSubscription = price.recurring !== null;

      // Create checkout session
      const sessionParams: Stripe.Checkout.SessionCreateParams = {
        customer: customerId,
        payment_method_types: ['card'],
        line_items: [
          {
            price: priceId,
            quantity: 1,
          },
        ],
        mode: isSubscription ? 'subscription' : 'payment',
        success_url: `${process.env.SUCCESS_URL}?session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${process.env.CANCEL_URL}`,
        metadata: {
          userId,
          extensionVersion,
          priceId,
        },
        // Enable promotional codes
        allow_promotion_codes: true,
        // Collect billing address for tax calculation
        billing_address_collection: 'auto',
      };

      // Add trial period if specified
      if (isSubscription && trialDays && trialDays > 0) {
        sessionParams.subscription_data = {
          trial_period_days: trialDays,
        };
      }

      const session = await stripe.checkout.sessions.create(sessionParams);

      res.json({
        sessionId: session.id,
        sessionUrl: session.url,
      });
    } catch (error) {
      console.error('Error creating checkout session:', error);
      res.status(500).json({ error: 'Failed to create checkout session' });
    }
  }
);

// ==========================================
// LICENSE VERIFICATION ENDPOINT
// ==========================================

app.get('/api/verify-license', async (req: Request, res: Response): Promise<void> => {
  try {
    const userId = req.query.userId as string;
    const licenseKey = req.query.licenseKey as string;

    if (!userId && !licenseKey) {
      res.status(400).json({ error: 'Either userId or licenseKey is required' });
      return;
    }

    let user: User | null = null;

    if (userId) {
      user = await getUserById(userId);
    } else if (licenseKey) {
      user = await getUserByLicenseKey(licenseKey);
    }

    if (!user) {
      res.status(404).json({ 
        hasLicense: false, 
        error: 'User not found' 
      });
      return;
    }

    // Check subscription status
    const hasActiveSubscription = 
      user.subscriptionStatus === 'active' || 
      user.subscriptionStatus === 'trialing';

    res.json({
      hasLicense: hasActiveSubscription,
      status: user.subscriptionStatus,
      tier: user.subscriptionTier,
      periodEnd: user.periodEnd,
      licenseKey: user.licenseKey,
    });
  } catch (error) {
    console.error('Error verifying license:', error);
    res.status(500).json({ error: 'Failed to verify license' });
  }
});

// ==========================================
// STRIPE WEBHOOK HANDLER
// ==========================================

async function handleStripeWebhook(req: Request, res: Response): Promise<void> {
  const sig = req.headers['stripe-signature'] as string;
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(req.body, sig, webhookSecret);
  } catch (err) {
    const error = err as Error;
    console.error(`Webhook signature verification failed: ${error.message}`);
    res.status(400).send(`Webhook Error: ${error.message}`);
    return;
  }

  // Handle the event
  try {
    await processStripeEvent(event);
  } catch (err) {
    const error = err as Error;
    console.error('Error processing webhook event:', error);
    // Still return 200 to prevent Stripe from retrying
  }

  res.json({ received: true });
}

async function processStripeEvent(event: Stripe.Event): Promise<void> {
  switch (event.type) {
    case 'checkout.session.completed': {
      const session = event.data.object as Stripe.Checkout.Session;
      await handleCheckoutComplete(session);
      break;
    }

    case 'customer.subscription.updated': {
      const subscription = event.data.object as Stripe.Subscription;
      await handleSubscriptionUpdate(subscription);
      break;
    }

    case 'customer.subscription.deleted': {
      const subscription = event.data.object as Stripe.Subscription;
      await handleSubscriptionDeleted(subscription);
      break;
    }

    case 'invoice.payment_failed': {
      const invoice = event.data.object as Stripe.Invoice;
      await handlePaymentFailed(invoice);
      break;
    }

    case 'invoice.payment_succeeded': {
      const invoice = event.data.object as Stripe.Invoice;
      await handlePaymentSucceeded(invoice);
      break;
    }

    default:
      console.log(`Unhandled event type: ${event.type}`);
  }
}

// ==========================================
// WEBHOOK EVENT HANDLERS
// ==========================================

async function handleCheckoutComplete(session: Stripe.Checkout.Session): Promise<void> {
  const { userId, priceId } = session.metadata || {};
  
  if (!userId) {
    console.error('No userId in checkout session metadata');
    return;
  }

  const customerId = session.customer as string;
  const customerEmail = session.customer_email;
  const isSubscription = session.mode === 'subscription';

  if (isSubscription) {
    const subscription = await stripe.subscriptions.retrieve(
      session.subscription as string
    );

    await updateUserSubscription(userId, {
      stripeCustomerId: customerId,
      email: customerEmail || undefined,
      status: subscription.status,
      subscriptionId: subscription.id,
      priceId,
      periodStart: new Date(subscription.current_period_start * 1000),
      periodEnd: new Date(subscription.current_period_end * 1000),
    });

    // Generate license key for the user
    const licenseKey = generateLicenseKey();
    await assignLicenseKey(userId, licenseKey);
  } else {
    // One-time purchase (lifetime license)
    await grantLifetimeAccess(userId, {
      stripeCustomerId: customerId,
      email: customerEmail || undefined,
      priceId,
    });

    // Generate lifetime license key
    const licenseKey = generateLicenseKey();
    await assignLicenseKey(userId, licenseKey, 'lifetime');
  }
}

async function handleSubscriptionUpdate(subscription: Stripe.Subscription): Promise<void> {
  const customerId = subscription.customer as string;
  const user = await getUserByCustomerId(customerId);

  if (!user) {
    console.error('No user found for customer:', customerId);
    return;
  }

  const priceId = subscription.items.data[0]?.price.id;

  await updateUserSubscription(user.id, {
    status: subscription.status,
    subscriptionId: subscription.id,
    priceId,
    periodStart: new Date(subscription.current_period_start * 1000),
    periodEnd: new Date(subscription.current_period_end * 1000),
    cancelAtPeriodEnd: subscription.cancel_at_period_end,
  });
}

async function handleSubscriptionDeleted(subscription: Stripe.Subscription): Promise<void> {
  const customerId = subscription.customer as string;
  const user = await getUserByCustomerId(customerId);

  if (!user) {
    console.error('No user found for customer:', customerId);
    return;
  }

  await revokeSubscription(user.id, 'subscription_canceled');
}

async function handlePaymentFailed(invoice: Stripe.Invoice): Promise<void> {
  const customerId = invoice.customer as string;
  const user = await getUserByCustomerId(customerId);

  if (!user) {
    console.error('No user found for customer:', customerId);
    return;
  }

  // Send notification to user
  await sendPaymentFailureNotification(user.email, {
    subscriptionId: invoice.subscription,
    amountDue: invoice.amount_due,
    nextPaymentAttempt: invoice.next_payment_attempt,
  });

  // Optionally update status to past_due
  await updateUserSubscription(user.id, { status: 'past_due' });
}

async function handlePaymentSucceeded(invoice: Stripe.Invoice): Promise<void> {
  const customerId = invoice.customer as string;
  const user = await getUserByCustomerId(customerId);

  if (!user) {
    return;
  }

  // Reset status if it was past_due
  if (user.subscriptionStatus === 'past_due') {
    await updateUserSubscription(user.id, { status: 'active' });
  }
}

// ==========================================
// LICENSE KEY GENERATION
// ==========================================

function generateLicenseKey(): string {
  const prefix = 'PRO';
  const timestamp = Date.now().toString(36).toUpperCase();
  const randomPart = crypto.randomBytes(4).toString('hex').toUpperCase();
  return `${prefix}-${timestamp}-${randomPart}`;
}

// ==========================================
// DATABASE HELPER FUNCTIONS (Implement according to your DB)
// ==========================================

async function getUserById(userId: string): Promise<User | null> {
  // Implement: Query your database for user by ID
  // This is a placeholder - replace with your actual database query
  console.log('Getting user by ID:', userId);
  return null;
}

async function getUserByLicenseKey(licenseKey: string): Promise<User | null> {
  // Implement: Query your database for user by license key
  console.log('Getting user by license key:', licenseKey);
  return null;
}

async function getUserByCustomerId(customerId: string): Promise<User | null> {
  // Implement: Query your database for user by Stripe customer ID
  console.log('Getting user by customer ID:', customerId);
  return null;
}

async function getStripeCustomerId(userId: string, email?: string): Promise<string | null> {
  // Implement: Get Stripe customer ID from your user record
  console.log('Getting Stripe customer ID for:', userId);
  return null;
}

async function linkUserToCustomer(userId: string, customerId: string): Promise<void> {
  // Implement: Link Stripe customer ID to user in your database
  console.log('Linking user', userId, 'to customer', customerId);
}

async function updateUserSubscription(userId: string, data: {
  stripeCustomerId?: string;
  email?: string;
  status?: string;
  subscriptionId?: string;
  priceId?: string;
  periodStart?: Date;
  periodEnd?: Date;
  cancelAtPeriodEnd?: boolean;
}): Promise<void> {
  // Implement: Update user subscription in your database
  console.log('Updating subscription for:', userId, data);
}

async function grantLifetimeAccess(userId: string, data: {
  stripeCustomerId: string;
  email?: string;
  priceId: string;
}): Promise<void> {
  // Implement: Grant lifetime access in your database
  console.log('Granting lifetime access to:', userId);
}

async function revokeSubscription(userId: string, reason: string): Promise<void> {
  // Implement: Revoke subscription in your database
  console.log('Revoking subscription for:', userId, 'reason:', reason);
}

async function assignLicenseKey(userId: string, licenseKey: string, type: 'subscription' | 'lifetime' = 'subscription'): Promise<void> {
  // Implement: Assign license key to user in your database
  console.log('Assigning license key:', licenseKey, 'to user:', userId);
}

async function sendPaymentFailureNotification(email: string, data: {
  subscriptionId?: string;
  amountDue: number;
  nextPaymentAttempt?: number;
}): Promise<void> {
  // Implement: Send email notification
  console.log('Sending payment failure notification to:', email, data);
}

// ==========================================
// ERROR HANDLING MIDDLEWARE
// ==========================================

app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  console.error('Unhandled error:', err);
  res.status(500).json({ error: 'Internal server error' });
});

// ==========================================
// START SERVER
// ==========================================

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
  console.log(`Webhook endpoint: /webhooks/stripe`);
});

export default app;
```

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

Update your extension's `manifest.json` to include necessary permissions. You'll need at minimum the [storage permission](https://theluckystrike.github.io/chrome-extension-guide/guides/chrome-extension-storage/) for caching subscription status and optionally [identity](https://theluckystrike.github.io/chrome-extension-guide/guides/chrome-extension-oauth2-authentication/) for retrieving the user's Google email.

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

## Complete TypeScript Extension Client: stripe-client.ts

Here's a production-ready TypeScript client for your Chrome extension:

```typescript
// stripe-client.ts - Complete TypeScript client for Stripe integration

import { LicenseService, LicenseStatus } from './license-service';

// ==========================================
// TYPE DEFINITIONS
// ==========================================

export interface SubscriptionStatus {
  hasLicense: boolean;
  status: 'free' | 'active' | 'trialing' | 'past_due' | 'canceled';
  tier?: string;
  periodEnd?: string;
  licenseKey?: string;
}

export interface CheckoutOptions {
  priceId: string;
  trialDays?: number;
}

export interface StorageKeys {
  userId: string;
  subscriptionStatus: string;
  subscriptionTier: string;
  periodEnd: string;
  licenseKey: string;
  cacheTimestamp: string;
}

// ==========================================
// STRIPE CLIENT SERVICE
// ==========================================

export class StripeClient {
  private apiBaseUrl: string;
  private licenseService: LicenseService;
  private cacheTTL: number = 3600000; // 1 hour in milliseconds

  constructor(apiBaseUrl: string) {
    this.apiBaseUrl = apiBaseUrl;
    this.licenseService = new LicenseService(apiBaseUrl);
  }

  // ==========================================
  // USER IDENTIFICATION
  // ==========================================

  /**
   * Get the user's identity. Tries chrome.identity first,
   * falls back to stored userId
   */
  async getUserId(): Promise<string | null> {
    // Try to get from storage first
    const stored = await this.getFromStorage('userId');
    if (stored) {
      return stored;
    }

    // Try chrome.identity if available
    try {
      const identity = await chrome.identity.getAuthToken({ interactive: false });
      if (identity) {
        // Extract email from token or use as-is
        const userId = identity;
        await this.saveToStorage('userId', userId);
        return userId;
      }
    } catch (error) {
      console.log('Identity API not available:', error);
    }

    return null;
  }

  // ==========================================
  // INITIATE CHECKOUT
  // ==========================================

  /**
   * Initiate the checkout process by creating a Stripe Checkout session
   */
  async initiateCheckout(options: CheckoutOptions): Promise<{ sessionUrl: string }> {
    const userId = await this.getUserId();
    
    if (!userId) {
      throw new Error('User not identified. Please sign in to continue.');
    }

    const manifest = chrome.runtime.getManifest();
    
    const response = await fetch(`${this.apiBaseUrl}/api/create-checkout-session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        priceId: options.priceId,
        userId: userId,
        extensionVersion: manifest.version,
        trialDays: options.trialDays,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Unknown error' }));
      throw new Error(error.error || `Server error: ${response.status}`);
    }

    const { sessionUrl } = await response.json();
    return { sessionUrl };
  }

  /**
   * Open Stripe Checkout in a new tab
   */
  async openCheckout(options: CheckoutOptions): Promise<void> {
    const { sessionUrl } = await this.initiateCheckout(options);
    await chrome.tabs.create({ url: sessionUrl });
  }

  // ==========================================
  // LICENSE VERIFICATION
  // ==========================================

  /**
   * Check if user has an active license
   */
  async checkLicenseStatus(): Promise<SubscriptionStatus> {
    const userId = await this.getUserId();
    
    if (!userId) {
      return { hasLicense: false, status: 'free' };
    }

    // Check cache first
    const cached = await this.getCachedStatus();
    if (cached && !this.isCacheExpired()) {
      return cached;
    }

    // Fetch fresh status from server
    const status = await this.licenseService.verifyLicense(userId);
    
    // Update cache
    await this.cacheStatus(status);
    
    return status;
  }

  /**
   * Validate license on extension startup
   */
  async validateOnStartup(): Promise<LicenseStatus> {
    const status = await this.checkLicenseStatus();
    
    if (status.hasLicense) {
      await this.updateExtensionAccess(true, status);
      return 'active';
    } else {
      await this.updateExtensionAccess(false);
      return 'inactive';
    }
  }

  // ==========================================
  // LICENSE KEY MANAGEMENT
  // ==========================================

  /**
   * Enter a license key manually
   */
  async activateLicenseKey(licenseKey: string): Promise<{ success: boolean; error?: string }> {
    const result = await this.licenseService.validateKey(licenseKey);
    
    if (result.hasLicense) {
      await this.saveToStorage('licenseKey', licenseKey);
      await this.cacheStatus({
        hasLicense: true,
        status: result.status,
        tier: result.tier,
        periodEnd: result.periodEnd,
        licenseKey,
      });
      await this.updateExtensionAccess(true, result);
      return { success: true };
    }
    
    return { success: false, error: result.error || 'Invalid license key' };
  }

  /**
   * Get the stored license key
   */
  async getLicenseKey(): Promise<string | null> {
    return this.getFromStorage('licenseKey');
  }

  // ==========================================
  // CROSS-DEVICE SYNC
  // ==========================================

  /**
   * Sync license status across devices using chrome.storage.sync
   */
  async syncAcrossDevices(userId: string): Promise<void> {
    const status = await this.licenseService.verifyLicense(userId);
    
    // Store in sync storage (automatically syncs across devices)
    await chrome.storage.sync.set({
      subscriptionStatus: status.status,
      subscriptionTier: status.tier || 'free',
      periodEnd: status.periodEnd || '',
      lastSync: Date.now(),
    });
  }

  // ==========================================
  // STORAGE HELPERS
  // ==========================================

  private async getFromStorage(key: string): Promise<string | null> {
    return new Promise((resolve) => {
      chrome.storage.local.get([key], (result) => {
        resolve(result[key] || null);
      });
    });
  }

  private async saveToStorage(key: string, value: string): Promise<void> {
    return new Promise((resolve) => {
      chrome.storage.local.set({ [key]: value }, resolve);
    });
  }

  private async getCachedStatus(): Promise<SubscriptionStatus | null> {
    const status = await this.getFromStorage('subscriptionStatus');
    const tier = await this.getFromStorage('subscriptionTier');
    const periodEnd = await this.getFromStorage('periodEnd');
    const licenseKey = await this.getFromStorage('licenseKey');

    if (!status) {
      return null;
    }

    return {
      hasLicense: status === 'active' || status === 'trialing',
      status: status as SubscriptionStatus['status'],
      tier,
      periodEnd,
      licenseKey,
    };
  }

  private async cacheStatus(status: SubscriptionStatus): Promise<void> {
    return new Promise((resolve) => {
      chrome.storage.local.set({
        subscriptionStatus: status.status,
        subscriptionTier: status.tier || '',
        periodEnd: status.periodEnd || '',
        licenseKey: status.licenseKey || '',
        cacheTimestamp: Date.now(),
      }, resolve);
    });
  }

  private isCacheExpired(): boolean {
    // This would need to be called differently due to async storage
    return false; // Simplified - implement proper async check
  }

  private async updateExtensionAccess(
    hasAccess: boolean, 
    status?: SubscriptionStatus
  ): Promise<void> {
    // Update extension badge or icon to indicate access
    const iconPath = hasAccess 
      ? 'images/icon-premium.png' 
      : 'images/icon-free.png';
    
    try {
      chrome.action.setIcon({ path: iconPath });
    } catch {
      // May not be a popup action
    }

    // Store the access state
    await this.saveToStorage('hasPremiumAccess', hasAccess ? 'true' : 'false');
  }
}

// ==========================================
// USAGE EXAMPLE
// ==========================================

/*
// In your background script or popup:
const stripeClient = new StripeClient('https://your-api.com');

// Check license on startup
chrome.runtime.onStartup.addListener(async () => {
  await stripeClient.validateOnStartup();
});

// Also check when extension is first installed
chrome.runtime.onInstalled.addListener(async () => {
  await stripeClient.validateOnStartup();
});

// Handle upgrade button click
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'INITIATE_UPGRADE') {
    stripeClient.openCheckout({ 
      priceId: message.priceId,
      trialDays: 14 
    })
      .then(() => sendResponse({ success: true }))
      .catch(error => sendResponse({ error: error.message }));
    return true;
  }
});
*/
```

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

## License Key System: LicenseService Class

For one-time purchases and manual license activation, you'll need a robust license key system. Here's a complete TypeScript implementation:

```typescript
// license-service.ts - License key generation and validation

import crypto from 'crypto';

export type LicenseStatus = 'active' | 'expired' | 'revoked' | 'invalid';

export interface LicenseInfo {
  hasLicense: boolean;
  status: LicenseStatus;
  tier?: string;
  periodEnd?: string;
  error?: string;
}

export interface LicenseValidationResult extends LicenseInfo {
  userId?: string;
  licenseKey: string;
  licenseType: 'subscription' | 'lifetime';
  issuedAt?: Date;
  expiresAt?: Date;
}

export class LicenseService {
  private apiBaseUrl: string;
  private licensePrefix: string = 'PRO';

  constructor(apiBaseUrl: string) {
    this.apiBaseUrl = apiBaseUrl;
  }

  // ==========================================
  // LICENSE KEY GENERATION
  // ==========================================

  /**
   * Generate a new license key
   * Format: PREFIX-TIMESTAMP-RANDOM
   * Example: PRO-ABC123-DEF456
   */
  generateKey(licenseType: 'subscription' | 'lifetime' = 'subscription'): string {
    const prefix = licenseType === 'lifetime' ? 'LIFE' : this.licensePrefix;
    const timestamp = Date.now().toString(36).toUpperCase();
    const randomBytes = crypto.randomBytes(4).toString('hex').toUpperCase();
    
    return `${prefix}-${timestamp}-${randomBytes}`;
  }

  /**
   * Generate a license key with custom prefix
   */
  generateKeyWithPrefix(prefix: string): string {
    const timestamp = Date.now().toString(36).toUpperCase();
    const randomBytes = crypto.randomBytes(4).toString('hex').toUpperCase();
    
    return `${prefix}-${timestamp}-${randomBytes}`;
  }

  // ==========================================
  // LICENSE VALIDATION
  // ==========================================

  /**
   * Validate a license key with the backend
   */
  async validateKey(licenseKey: string): Promise<LicenseValidationResult> {
    try {
      const response = await fetch(
        `${this.apiBaseUrl}/api/verify-license?licenseKey=${encodeURIComponent(licenseKey)}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        return {
          hasLicense: false,
          status: 'invalid',
          licenseKey,
          licenseType: 'subscription',
          error: `Server error: ${response.status}`,
        };
      }

      const data = await response.json();
      
      return {
        hasLicense: data.hasLicense,
        status: data.hasLicense ? 'active' : 'invalid',
        tier: data.tier,
        periodEnd: data.periodEnd,
        licenseKey,
        licenseType: data.licenseType || 'subscription',
        expiresAt: data.periodEnd ? new Date(data.periodEnd) : undefined,
      };
    } catch (error) {
      return {
        hasLicense: false,
        status: 'invalid',
        licenseKey,
        licenseType: 'subscription',
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  /**
   * Verify license by user ID
   */
  async verifyLicense(userId: string): Promise<LicenseInfo> {
    try {
      const response = await fetch(
        `${this.apiBaseUrl}/api/verify-license?userId=${encodeURIComponent(userId)}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        return {
          hasLicense: false,
          status: 'invalid',
          error: `Server error: ${response.status}`,
        };
      }

      const data = await response.json();
      
      return {
        hasLicense: data.hasLicense,
        status: data.hasLicense ? 'active' : 'invalid',
        tier: data.tier,
        periodEnd: data.periodEnd,
      };
    } catch (error) {
      return {
        hasLicense: false,
        status: 'invalid',
        error: error instanceof Error ? error.message : 'Network error',
      };
    }
  }

  // ==========================================
  // LICENSE KEY OPERATIONS
  // ==========================================

  /**
   * Revoke a license key (admin operation)
   */
  async revokeKey(licenseKey: string, reason: string): Promise<{ success: boolean; error?: string }> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/admin/revoke-license`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // Add admin authentication header
        },
        body: JSON.stringify({ licenseKey, reason }),
      });

      if (!response.ok) {
        return { success: false, error: `Server error: ${response.status}` };
      }

      return { success: true };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Network error' 
      };
    }
  }

  /**
   * Refresh/extend a license key
   */
  async refreshKey(licenseKey: string): Promise<{ success: boolean; newExpiry?: string; error?: string }> {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/refresh-license`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ licenseKey }),
      });

      if (!response.ok) {
        return { success: false, error: `Server error: ${response.status}` };
      }

      const data = await response.json();
      return { success: true, newExpiry: data.newExpiry };
    } catch (error) {
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Network error' 
      };
    }
  }

  // ==========================================
  // UTILITY METHODS
  // ==========================================

  /**
   * Validate license key format (client-side check)
   */
  validateKeyFormat(licenseKey: string): boolean {
    const formatRegex = /^[A-Z0-9]{3,5}-[A-Z0-9]{5,}-[A-Z0-9]{8}$/i;
    return formatRegex.test(licenseKey);
  }

  /**
   * Check if license is expired (client-side)
   */
  isExpired(periodEnd?: string): boolean {
    if (!periodEnd) return false;
    return new Date(periodEnd) < new Date();
  }

  /**
   * Get days until expiration
   */
  getDaysUntilExpiry(periodEnd?: string): number | null {
    if (!periodEnd) return null;
    
    const now = new Date();
    const expiry = new Date(periodEnd);
    const diffTime = expiry.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return diffDays;
  }
}
```

### Using License Keys in Your Extension

```typescript
// Example usage in your extension popup

import { LicenseService } from './license-service';

const licenseService = new LicenseService('https://your-api.com');

// Check if user has active license
async function checkAccess() {
  const userId = await getUserId();
  if (userId) {
    const result = await licenseService.verifyLicense(userId);
    if (result.hasLicense) {
      showPremiumFeatures();
    } else {
      showUpgradePrompt();
    }
  }
}

// Manual license key activation
async function activateLicense(keyInput: string) {
  // First validate format client-side
  if (!licenseService.validateKeyFormat(keyInput)) {
    showError('Invalid license key format');
    return;
  }

  // Then validate with server
  const result = await licenseService.validateKey(keyInput);
  if (result.hasLicense) {
    await saveToStorage('licenseKey', keyInput);
    showSuccess('License activated!');
    showPremiumFeatures();
  } else {
    showError(result.error || 'Invalid license key');
  }
}

// Check expiration
async function checkExpiration() {
  const periodEnd = await getFromStorage('periodEnd');
  if (periodEnd) {
    const daysLeft = licenseService.getDaysUntilExpiry(periodEnd);
    if (daysLeft !== null && daysLeft <= 7 && daysLeft > 0) {
      showRenewalReminder(`Your license expires in ${daysLeft} days`);
    }
  }
}
```

## Security Considerations

Securing your Stripe integration is critical because it directly controls access to your premium features. This section covers essential security practices for extension payment systems.

### Never Expose Stripe Secret Keys

The most critical security rule: your Stripe secret key (`sk_live_...`) must never appear in your extension code. Chrome extensions are client-side software that can be easily inspected, decompiled, and modified. Anyone viewing your extension's source can extract hardcoded keys.

**What NOT to do:**
```typescript
// ❌ NEVER do this in your extension
const STRIPE_SECRET = 'sk_live_xxxxx'; // Attackers will find this!
stripe.charges.create({ ... }); // This exposes your key
```

**What you MUST do:**
```typescript
// ✅ Always proxy through your backend
// Extension code (background.ts):
const response = await fetch('https://your-api.com/api/create-checkout-session', {
  method: 'POST',
  body: JSON.stringify({ priceId: 'price_xxx' })
});
// Backend handles all Stripe communication
```

Your backend server holds the secret key and only exposes public endpoints to your extension.

### Validate Webhook Signatures

Stripe webhooks can be spoofed by attackers trying to grant themselves free access. Always verify webhook signatures:

```typescript
// server.ts - Essential webhook verification
app.post('/webhooks/stripe', express.raw({ type: 'application/json' }), 
  async (req, res) => {
    const sig = req.headers['stripe-signature'];
    
    try {
      const event = stripe.webhooks.constructEvent(
        req.body,
        sig,
        process.env.STRIPE_WEBHOOK_SECRET
      );
      // Process event only if signature is valid
    } catch (err) {
      // Invalid signature - possible attack!
      console.error('Webhook signature verification failed');
      return res.status(400).send('Invalid signature');
    }
  }
);
```

### Rate Limit API Endpoints

Protect your backend from abuse by implementing rate limiting:

```typescript
// server.ts - Rate limiting
import rateLimit from 'express-rate-limit';

const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  message: { error: 'Too many requests' },
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/api/', apiLimiter);

// Stricter limits for sensitive endpoints
const checkoutLimiter = rateLimit({
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 10, // 10 checkout attempts per hour
});

app.use('/api/create-checkout-session', checkoutLimiter);
```

### Configure CORS Properly

Restrict which origins can access your API:

```typescript
// server.ts - CORS configuration
app.use(cors({
  origin: (origin, callback) => {
    // Allow your extension IDs (both Chrome Web Store and dev)
    const allowedOrigins = [
      'chrome-extension://YOUR_EXTENSION_ID',
      'chrome-extension://YOUR_DEV_EXTENSION_ID',
      'https://your-website.com',
    ];
    
    // Allow no-origin requests (curl, server-to-server)
    if (!origin || allowedOrigins.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
}));
```

### Content Security Policy for Extension

Configure your extension's CSP to allow necessary network requests:

```json
// manifest.json
{
  "content_security_policy": {
    "extension_pages": "script-src 'self'; object-src 'self'; connect-src https://your-api.com https://api.stripe.com"
  }
}
```

### Additional Security Best Practices

1. **Use HTTPS exclusively**: All production traffic must use TLS 1.2+

2. **Rotate API keys periodically**: Generate new Stripe keys annually and revoke old ones

3. **Log all payment events**: Maintain audit trails for troubleshooting and fraud detection

4. **Implement idempotent webhook processing**: Use event IDs to prevent duplicate processing

5. **Sanitize error messages**: Never expose internal system details to users

```typescript
// ✅ Good error handling
catch (error) {
  console.error('Payment error:', error); // Internal logging
  res.status(500).json({ error: 'Payment failed. Please try again.' }); // User-facing
}

// ❌ Bad error handling
catch (error) {
  res.status(500).json({ error: error.message }); // Exposes internals!
}
```

## Going Live Checklist

Before launching your extension with Stripe payments, complete this checklist to ensure a smooth production rollout.

### 1. Switch to Live API Keys

- [ ] Generate live Stripe API keys in the Dashboard
- [ ] Update backend environment variables:
  ```
  STRIPE_SECRET_KEY=sk_live_xxxxx
  STRIPE_PUBLISHABLE_KEY=pk_live_xxxxx
  STRIPE_WEBHOOK_SECRET=whsec_xxxxx
  ```
- [ ] Verify test keys are no longer in use
- [ ] Remove any test-only code paths

### 2. Configure Webhooks for Production

- [ ] Add production webhook endpoint in Stripe Dashboard
- [ ] Select all required events:
  - `checkout.session.completed`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_failed`
  - `invoice.payment_succeeded`
- [ ] Test webhook delivery with Stripe CLI
- [ ] Set up webhook retry notifications

### 3. Enable Stripe Tax (if selling globally)

- [ ] Enable Stripe Tax in Dashboard
- [ ] Configure tax behavior (inclusive vs exclusive)
- [ ] Set up product tax codes
- [ ] Test with different customer locations

### 4. Configure Customer Portal

- [ ] Enable Customer Portal in Stripe Dashboard
- [ ] Customize portal settings:
  - Allow subscription updates
  - Enable invoice history
  - Configure cancellation flow
- [ ] Add portal link to extension settings

### 5. Test with Real Cards

- [ ] Process a test payment with your own card
- [ ] Verify webhook fires and processes correctly
- [ ] Check that extension unlocks after payment
- [ ] Test the complete user flow:
  1. Install extension
  2. Click upgrade
  3. Complete payment
  4. Verify premium access

### 6. Set Up Monitoring

- [ ] Configure Stripe Dashboard alerts:
  - New subscription
  - Failed payment
  - Churned customer
- [ ] Set up error tracking (Sentry, LogRocket)
- [ ] Create status page for your API

### 7. Prepare Support Resources

- [ ] Create FAQ for common billing questions
- [ ] Set up refund request process
- [ ] Prepare email templates for:
  - Welcome/payment confirmation
  - Payment failure warning
  - Subscription cancellation

### 8. Review Legal Compliance

- [ ] Add Terms of Service link
- [ ] Add Privacy Policy (especially for EU users)
- [ ] Include refund policy
- [ ] Display prices in local currency

### 9. Extension Store Submission

- [ ] Update extension listing with pricing info
- [ ] Add "Remove Ads" or "Premium" descriptions
- [ ] Create screenshots showing upgrade flow
- [ ] Submit to Chrome Web Store

### Post-Launch Monitoring

After launch, monitor these metrics weekly:

- **Conversion rate**: Purchases ÷ unique visitors
- **Churn rate**: Cancellations ÷ active subscribers
- **Payment failure rate**: Failed payments ÷ total attempts
- **Revenue**: Total processed payments
- **Support tickets**: Billing-related inquiries

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

## Technical Deep Dive

For the code behind these strategies, see the companion [Chrome Extension Guide](https://theluckystrike.github.io/chrome-extension-guide/):

### Background Processing
- [Background Service Workers](https://theluckystrike.github.io/chrome-extension-guide/guides/chrome-extension-background-service-worker/) — Handling payment callbacks in MV3
- [Background Patterns](https://theluckystrike.github.io/chrome-extension-guide/guides/background-patterns/) — Common background patterns
- [Service Worker Lifecycle](https://theluckystrike.github.io/chrome-extension-guide/guides/service-worker-lifecycle/) — Lifecycle management

### Network & API
- [Fetch API Patterns](https://github.com/theluckystrike/chrome-extension-guide/blob/main/docs/patterns/fetch-patterns.md) — Making server requests securely
- [Fetch Interceptor](https://github.com/theluckystrike/chrome-extension-guide/blob/main/docs/patterns/fetch-interceptor.md) — Intercept API calls
- [Message Passing](https://theluckystrike.github.io/chrome-extension-guide/guides/chrome-extension-messaging/) — Communicate with backend

### Storage & Caching
- [Storage API Tutorial](https://theluckystrike.github.io/chrome-extension-guide/guides/chrome-extension-storage/) — Cache subscription status
- [Storage Sync vs Local](https://theluckystrike.github.io/chrome-extension-guide/guides/chrome-extension-storage-api-tutorial-sync-vs-local/) — Choose the right storage
- [Advanced Storage Patterns](https://theluckystrike.github.io/chrome-extension-guide/guides/advanced-storage-patterns/) — Caching strategies

### Authentication
- [OAuth2 Authentication](https://theluckystrike.github.io/chrome-extension-guide/guides/chrome-extension-oauth2-authentication/) — Google identity
- [Authentication Patterns](https://github.com/theluckystrike/chrome-extension-guide/blob/main/docs/patterns/authentication-patterns.md) — User identity management

### Security
- [Content Security Policy](https://github.com/theluckystrike/chrome-extension-guide/blob/main/docs/mv3/content-security-policy.md) — CSP configuration
- [Security Best Practices](https://theluckystrike.github.io/chrome-extension-guide/guides/security-best-practices/) — Extension security

All tools and guides are part of the [Zovo](https://zovo.one) ecosystem.

---

## Related Articles

- [Freemium Model](/articles/freemium-model/) — Implementing free tier with premium upgrades
- [Subscription Model](/articles/subscription-model/) — Managing recurring revenue
- [License Key System](/articles/license-key-system/) — Implementing license keys for one-time purchases
- [Chrome Web Store Payments](articles/chrome-web-store-payments.md)
- [Server Side Validation](articles/server-side-validation.md)


---

Part of the Extension Monetization Playbook by theluckystrike. Professional Chrome extension development at zovo.one

---

Built by [Zovo](https://zovo.one) - Open-source tools and guides for extension developers.


## Related Articles

- [Zero To 1000 Users](docs/growth/zero-to-1000-users/)
- [Update Monetization](articles/update-monetization/)
- [Freemium Model](docs/revenue/freemium-model/)



---

Part of the Extension Monetization Playbook by theluckystrike. Chrome extension development services at zovo.one.
