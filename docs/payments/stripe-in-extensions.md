---
layout: default
title: "Stripe Integration for Chrome Extensions: Complete Guide"
description: "Complete guide to integrating Stripe payments in Chrome extensions. Checkout, subscriptions, and webhooks."
permalink: /payments/stripe-in-extensions/
---
# How to Integrate Stripe Payments in Chrome Extensions

Stripe is the standard payment processor for Chrome extension businesses. It handles subscriptions, one-time payments, invoicing, and tax calculation through well-documented APIs and a developer-friendly dashboard. This guide covers the complete integration from creating checkout sessions in a background service worker through webhook processing, license validation, subscription lifecycle management, testing with the Stripe CLI, and PCI compliance considerations specific to browser extensions.

Chrome extensions cannot process payments directly. The extension runs in the browser sandbox with no server-side capability, so all payment logic flows through your backend API. The extension initiates payment flows by opening Stripe Checkout in a new tab, then polls or listens for confirmation that the payment succeeded. Your backend handles all sensitive operations: creating checkout sessions, processing webhooks, validating licenses, and managing subscription changes.

This architecture keeps your Stripe secret key on the server, ensures PCI compliance, and provides a reliable payment experience regardless of the user's browser state.

---

## Architecture Overview

The payment flow for a Chrome extension follows this pattern:

1. User clicks "Upgrade" in the extension popup or options page.
2. Extension sends a request to your backend API to create a Stripe Checkout session.
3. Backend creates the session with Stripe and returns the session URL.
4. Extension opens the Checkout URL in a new browser tab.
5. User completes payment on the Stripe-hosted Checkout page.
6. Stripe sends a webhook to your backend confirming payment.
7. Backend activates the user's license and stores subscription data.
8. Extension detects the license change and unlocks premium features.

This flow keeps all sensitive operations server-side while providing a seamless user experience. The extension never touches credit card data, API secret keys, or subscription management logic directly.

---

## Complete Stripe Checkout Integration with Background Service Worker

The background service worker is the ideal place to coordinate payment flows because it persists across popup opens and closes. If the user closes the popup after clicking "Upgrade," the service worker continues monitoring for payment completion.

### Backend: Create Checkout Session Endpoint

```typescript
// server/routes/checkout.ts — Express route for creating Stripe Checkout sessions

import Stripe from 'stripe';
import { Request, Response } from 'express';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-04-10',
});

interface CreateCheckoutBody {
  extensionUserId: string;
  email: string;
  priceId: string;
  successUrl?: string;
  cancelUrl?: string;
}

export async function createCheckoutSession(
  req: Request<unknown, unknown, CreateCheckoutBody>,
  res: Response
): Promise<void> {
  const { extensionUserId, email, priceId, successUrl, cancelUrl } = req.body;

  try {
    // Find or create the Stripe customer
    let customer: Stripe.Customer;
    const existingCustomers = await stripe.customers.list({
      email,
      limit: 1,
    });

    if (existingCustomers.data.length > 0) {
      customer = existingCustomers.data[0];
    } else {
      customer = await stripe.customers.create({
        email,
        metadata: {
          extensionUserId,
          source: 'chrome_extension',
        },
      });
    }

    // Create the checkout session
    const session = await stripe.checkout.sessions.create({
      customer: customer.id,
      payment_method_types: ['card'],
      line_items: [
        {
          price: priceId,
          quantity: 1,
        },
      ],
      mode: 'subscription',
      success_url:
        successUrl ||
        `${process.env.APP_URL}/payment/success?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url:
        cancelUrl || `${process.env.APP_URL}/payment/canceled`,
      subscription_data: {
        metadata: {
          extensionUserId,
        },
      },
      allow_promotion_codes: true,
      billing_address_collection: 'auto',
      tax_id_collection: {
        enabled: true,
      },
    });

    res.json({
      sessionId: session.id,
      url: session.url,
    });
  } catch (error) {
    console.error('Checkout session creation failed:', error);
    res.status(500).json({ error: 'Failed to create checkout session' });
  }
}
```

### Extension: Background Service Worker Payment Coordinator

```typescript
// extension/background/payment.ts — Service worker payment flow coordinator

const API_BASE = 'https://your-api.com';

interface CheckoutResponse {
  sessionId: string;
  url: string;
}

interface LicenseStatus {
  valid: boolean;
  plan: 'free' | 'pro' | 'team';
  expiresAt: string | null;
  customerId: string | null;
}

// Create a checkout session and open it in a new tab
async function initiateCheckout(priceId: string): Promise<void> {
  const { userId, email } = await chrome.storage.local.get(['userId', 'email']);

  if (!userId || !email) {
    // Redirect to sign-in first
    chrome.tabs.create({ url: `${API_BASE}/auth/signin` });
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/api/checkout/create`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        extensionUserId: userId,
        email,
        priceId,
      }),
    });

    if (!response.ok) {
      throw new Error(`Checkout creation failed: ${response.status}`);
    }

    const data: CheckoutResponse = await response.json();

    // Open Stripe Checkout in a new tab
    const tab = await chrome.tabs.create({ url: data.url });

    // Start polling for payment completion
    pollForPaymentCompletion(data.sessionId, tab.id);
  } catch (error) {
    console.error('Checkout initiation failed:', error);
    // Notify the popup of the failure
    chrome.runtime.sendMessage({
      action: 'checkoutError',
      message: 'Payment could not be initiated. Please try again.',
    });
  }
}

// Poll the backend to check if payment completed
async function pollForPaymentCompletion(
  sessionId: string,
  tabId: number | undefined
): Promise<void> {
  const maxAttempts = 60; // 5 minutes at 5-second intervals
  let attempts = 0;

  const checkPayment = async (): Promise<void> => {
    attempts++;

    try {
      const response = await fetch(
        `${API_BASE}/api/checkout/status/${sessionId}`
      );
      const data = await response.json();

      if (data.status === 'complete') {
        // Payment succeeded — update local license
        await chrome.storage.local.set({
          licenseStatus: {
            valid: true,
            plan: data.plan,
            expiresAt: data.expiresAt,
            customerId: data.customerId,
          },
        });

        // Notify all extension views
        chrome.runtime.sendMessage({
          action: 'paymentComplete',
          plan: data.plan,
        });

        // Close the Stripe Checkout tab if still open
        if (tabId) {
          chrome.tabs.remove(tabId).catch(() => {});
        }

        return;
      }

      if (data.status === 'expired' || attempts >= maxAttempts) {
        chrome.runtime.sendMessage({
          action: 'checkoutExpired',
          message: 'The checkout session has expired.',
        });
        return;
      }

      // Keep polling
      setTimeout(checkPayment, 5000);
    } catch {
      if (attempts < maxAttempts) {
        setTimeout(checkPayment, 5000);
      }
    }
  };

  // Start polling after a short delay
  setTimeout(checkPayment, 3000);
}

// Listen for messages from the popup or options page
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.action === 'startCheckout') {
    initiateCheckout(message.priceId);
    sendResponse({ status: 'initiated' });
  }

  if (message.action === 'getLicenseStatus') {
    getLicenseStatus().then(sendResponse);
    return true; // Keep channel open for async response
  }
});

// Validate license status against the server
async function getLicenseStatus(): Promise<LicenseStatus> {
  const cached = await chrome.storage.local.get('licenseStatus');

  // Return cached status if checked within the last hour
  const lastCheck = await chrome.storage.local.get('lastLicenseCheck');
  if (
    cached.licenseStatus &&
    lastCheck.lastLicenseCheck &&
    Date.now() - lastCheck.lastLicenseCheck < 3600000
  ) {
    return cached.licenseStatus;
  }

  // Validate with server
  try {
    const { userId } = await chrome.storage.local.get('userId');
    if (!userId) return { valid: false, plan: 'free', expiresAt: null, customerId: null };

    const response = await fetch(
      `${API_BASE}/api/license/validate?userId=${userId}`
    );
    const status: LicenseStatus = await response.json();

    await chrome.storage.local.set({
      licenseStatus: status,
      lastLicenseCheck: Date.now(),
    });

    return status;
  } catch {
    // Offline or server error — use cached status
    return (
      cached.licenseStatus || {
        valid: false,
        plan: 'free',
        expiresAt: null,
        customerId: null,
      }
    );
  }
}
```

---

## Webhook Handling

Webhooks are how Stripe notifies your backend about payment events. Every critical subscription event — successful payment, failed payment, cancellation, plan change — arrives as a webhook. Your webhook handler must be idempotent (safe to process the same event multiple times) and must verify the webhook signature to prevent spoofing.

```typescript
// server/routes/webhooks.ts — Stripe webhook handler

import Stripe from 'stripe';
import { Request, Response } from 'express';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-04-10',
});

const endpointSecret = process.env.STRIPE_WEBHOOK_SECRET!;

export async function handleWebhook(
  req: Request,
  res: Response
): Promise<void> {
  const sig = req.headers['stripe-signature'] as string;

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(req.body, sig, endpointSecret);
  } catch (err) {
    console.error('Webhook signature verification failed:', err);
    res.status(400).send('Webhook signature verification failed');
    return;
  }

  try {
    switch (event.type) {
      case 'checkout.session.completed': {
        const session = event.data.object as Stripe.Checkout.Session;
        await handleCheckoutCompleted(session);
        break;
      }
      case 'customer.subscription.updated': {
        const subscription = event.data.object as Stripe.Subscription;
        await handleSubscriptionUpdated(subscription);
        break;
      }
      case 'customer.subscription.deleted': {
        const subscription = event.data.object as Stripe.Subscription;
        await handleSubscriptionCanceled(subscription);
        break;
      }
      case 'invoice.payment_failed': {
        const invoice = event.data.object as Stripe.Invoice;
        await handlePaymentFailed(invoice);
        break;
      }
      case 'invoice.paid': {
        const invoice = event.data.object as Stripe.Invoice;
        await handleInvoicePaid(invoice);
        break;
      }
      default:
        console.log(`Unhandled event type: ${event.type}`);
    }

    res.json({ received: true });
  } catch (error) {
    console.error(`Error processing webhook ${event.type}:`, error);
    res.status(500).json({ error: 'Webhook processing failed' });
  }
}

async function handleCheckoutCompleted(
  session: Stripe.Checkout.Session
): Promise<void> {
  const extensionUserId = session.metadata?.extensionUserId;
  if (!extensionUserId) return;

  const subscriptionId = session.subscription as string;
  const customerId = session.customer as string;

  // Store the subscription in your database
  await db.licenses.upsert({
    where: { extensionUserId },
    update: {
      stripeCustomerId: customerId,
      stripeSubscriptionId: subscriptionId,
      plan: 'pro',
      status: 'active',
      activatedAt: new Date(),
    },
    create: {
      extensionUserId,
      stripeCustomerId: customerId,
      stripeSubscriptionId: subscriptionId,
      plan: 'pro',
      status: 'active',
      activatedAt: new Date(),
    },
  });
}

async function handleSubscriptionUpdated(
  subscription: Stripe.Subscription
): Promise<void> {
  const extensionUserId = subscription.metadata?.extensionUserId;
  if (!extensionUserId) return;

  const plan = determinePlanFromSubscription(subscription);
  const status = subscription.status === 'active' ? 'active' : 'inactive';

  await db.licenses.update({
    where: { extensionUserId },
    data: {
      plan,
      status,
      currentPeriodEnd: new Date(subscription.current_period_end * 1000),
    },
  });
}

async function handleSubscriptionCanceled(
  subscription: Stripe.Subscription
): Promise<void> {
  const extensionUserId = subscription.metadata?.extensionUserId;
  if (!extensionUserId) return;

  // Keep access until the end of the billing period
  await db.licenses.update({
    where: { extensionUserId },
    data: {
      status: 'canceled',
      canceledAt: new Date(),
      accessUntil: new Date(subscription.current_period_end * 1000),
    },
  });
}

async function handlePaymentFailed(invoice: Stripe.Invoice): Promise<void> {
  const customerId = invoice.customer as string;
  const license = await db.licenses.findFirst({
    where: { stripeCustomerId: customerId },
  });

  if (license) {
    await db.licenses.update({
      where: { id: license.id },
      data: {
        status: 'past_due',
        lastPaymentFailedAt: new Date(),
      },
    });

    // Optionally send a notification to the extension
    // via your push notification system
  }
}

async function handleInvoicePaid(invoice: Stripe.Invoice): Promise<void> {
  const customerId = invoice.customer as string;
  const license = await db.licenses.findFirst({
    where: { stripeCustomerId: customerId },
  });

  if (license && license.status === 'past_due') {
    await db.licenses.update({
      where: { id: license.id },
      data: { status: 'active' },
    });
  }
}

function determinePlanFromSubscription(
  subscription: Stripe.Subscription
): string {
  const priceId = subscription.items.data[0]?.price.id;
  const planMap: Record<string, string> = {
    [process.env.STRIPE_PRICE_PRO_MONTHLY!]: 'pro',
    [process.env.STRIPE_PRICE_PRO_ANNUAL!]: 'pro',
    [process.env.STRIPE_PRICE_TEAM_MONTHLY!]: 'team',
    [process.env.STRIPE_PRICE_TEAM_ANNUAL!]: 'team',
  };
  return planMap[priceId] || 'pro';
}
```

---

## License Validation

License validation is the mechanism by which your extension confirms that a user has an active subscription. The validation must be resilient to network failures, fast enough to avoid user-visible delays, and secure against tampering.

```typescript
// server/routes/license.ts — License validation endpoint

import { Request, Response } from 'express';

interface LicenseResponse {
  valid: boolean;
  plan: string;
  expiresAt: string | null;
  customerId: string | null;
  features: string[];
}

export async function validateLicense(
  req: Request,
  res: Response
): Promise<void> {
  const { userId } = req.query;

  if (!userId || typeof userId !== 'string') {
    res.status(400).json({ valid: false, plan: 'free', expiresAt: null, customerId: null, features: [] });
    return;
  }

  try {
    const license = await db.licenses.findUnique({
      where: { extensionUserId: userId },
    });

    if (!license || license.status === 'canceled') {
      // Check if canceled user still has access until period end
      if (
        license?.accessUntil &&
        new Date(license.accessUntil) > new Date()
      ) {
        res.json({
          valid: true,
          plan: license.plan,
          expiresAt: license.accessUntil.toISOString(),
          customerId: license.stripeCustomerId,
          features: getFeaturesForPlan(license.plan),
        });
        return;
      }

      res.json({
        valid: false,
        plan: 'free',
        expiresAt: null,
        customerId: null,
        features: getFeaturesForPlan('free'),
      });
      return;
    }

    // Grace period for past_due: give 7 days before revoking access
    if (license.status === 'past_due') {
      const gracePeriodMs = 7 * 24 * 60 * 60 * 1000;
      const failedAt = license.lastPaymentFailedAt?.getTime() || 0;
      const graceExpired = Date.now() - failedAt > gracePeriodMs;

      if (graceExpired) {
        res.json({
          valid: false,
          plan: 'free',
          expiresAt: null,
          customerId: license.stripeCustomerId,
          features: getFeaturesForPlan('free'),
        });
        return;
      }
    }

    res.json({
      valid: true,
      plan: license.plan,
      expiresAt: license.currentPeriodEnd?.toISOString() || null,
      customerId: license.stripeCustomerId,
      features: getFeaturesForPlan(license.plan),
    });
  } catch (error) {
    console.error('License validation error:', error);
    res.status(500).json({ valid: false, plan: 'free', expiresAt: null, customerId: null, features: [] });
  }
}

function getFeaturesForPlan(plan: string): string[] {
  const features: Record<string, string[]> = {
    free: ['basic-search', 'tab-groups', 'session-save'],
    pro: ['basic-search', 'tab-groups', 'session-save', 'cloud-sync', 'auto-suspend', 'custom-rules'],
    team: ['basic-search', 'tab-groups', 'session-save', 'cloud-sync', 'auto-suspend', 'custom-rules', 'team-sharing', 'admin-panel'],
  };
  return features[plan] || features['free'];
}
```

---

## Subscription Management: Upgrade, Downgrade, Cancel, Reactivate

Subscription lifecycle management handles every state change a subscriber might initiate. Each operation maps to a Stripe API call, and your backend must update your local database to match.

```typescript
// server/routes/subscription.ts — Subscription management endpoints

import Stripe from 'stripe';
import { Request, Response } from 'express';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2024-04-10',
});

// Upgrade: Switch to a higher-tier plan
export async function upgradeSubscription(
  req: Request,
  res: Response
): Promise<void> {
  const { extensionUserId, newPriceId } = req.body;

  const license = await db.licenses.findUnique({
    where: { extensionUserId },
  });

  if (!license?.stripeSubscriptionId) {
    res.status(404).json({ error: 'No active subscription found' });
    return;
  }

  const subscription = await stripe.subscriptions.retrieve(
    license.stripeSubscriptionId
  );

  // Upgrade immediately with prorated billing
  const updatedSubscription = await stripe.subscriptions.update(
    license.stripeSubscriptionId,
    {
      items: [
        {
          id: subscription.items.data[0].id,
          price: newPriceId,
        },
      ],
      proration_behavior: 'create_prorations',
    }
  );

  await db.licenses.update({
    where: { extensionUserId },
    data: {
      plan: determinePlanFromSubscription(updatedSubscription),
      currentPeriodEnd: new Date(
        updatedSubscription.current_period_end * 1000
      ),
    },
  });

  res.json({ success: true, plan: determinePlanFromSubscription(updatedSubscription) });
}

// Downgrade: Switch to a lower-tier plan at end of current period
export async function downgradeSubscription(
  req: Request,
  res: Response
): Promise<void> {
  const { extensionUserId, newPriceId } = req.body;

  const license = await db.licenses.findUnique({
    where: { extensionUserId },
  });

  if (!license?.stripeSubscriptionId) {
    res.status(404).json({ error: 'No active subscription found' });
    return;
  }

  const subscription = await stripe.subscriptions.retrieve(
    license.stripeSubscriptionId
  );

  // Schedule downgrade for end of current billing period
  await stripe.subscriptions.update(license.stripeSubscriptionId, {
    items: [
      {
        id: subscription.items.data[0].id,
        price: newPriceId,
      },
    ],
    proration_behavior: 'none',
    billing_cycle_anchor: 'unchanged',
  });

  res.json({
    success: true,
    message: 'Plan will be downgraded at the end of the current billing period.',
    effectiveDate: new Date(subscription.current_period_end * 1000).toISOString(),
  });
}

// Cancel: End subscription at period end (not immediately)
export async function cancelSubscription(
  req: Request,
  res: Response
): Promise<void> {
  const { extensionUserId } = req.body;

  const license = await db.licenses.findUnique({
    where: { extensionUserId },
  });

  if (!license?.stripeSubscriptionId) {
    res.status(404).json({ error: 'No active subscription found' });
    return;
  }

  // Cancel at period end — user keeps access until then
  const subscription = await stripe.subscriptions.update(
    license.stripeSubscriptionId,
    { cancel_at_period_end: true }
  );

  await db.licenses.update({
    where: { extensionUserId },
    data: {
      status: 'canceled',
      canceledAt: new Date(),
      accessUntil: new Date(subscription.current_period_end * 1000),
    },
  });

  res.json({
    success: true,
    accessUntil: new Date(subscription.current_period_end * 1000).toISOString(),
    message: 'Your subscription has been canceled. You retain access until the end of your billing period.',
  });
}

// Reactivate: Un-cancel a subscription that was set to cancel at period end
export async function reactivateSubscription(
  req: Request,
  res: Response
): Promise<void> {
  const { extensionUserId } = req.body;

  const license = await db.licenses.findUnique({
    where: { extensionUserId },
  });

  if (!license?.stripeSubscriptionId) {
    res.status(404).json({ error: 'No subscription found' });
    return;
  }

  const subscription = await stripe.subscriptions.retrieve(
    license.stripeSubscriptionId
  );

  // Only reactivate if the subscription hasn't actually ended yet
  if (subscription.status === 'active' && subscription.cancel_at_period_end) {
    await stripe.subscriptions.update(license.stripeSubscriptionId, {
      cancel_at_period_end: false,
    });

    await db.licenses.update({
      where: { extensionUserId },
      data: {
        status: 'active',
        canceledAt: null,
        accessUntil: null,
      },
    });

    res.json({ success: true, message: 'Your subscription has been reactivated.' });
    return;
  }

  // If subscription has already ended, create a new checkout session
  if (
    subscription.status === 'canceled' ||
    subscription.status === 'incomplete_expired'
  ) {
    res.json({
      success: false,
      requiresNewCheckout: true,
      message: 'Your subscription has ended. Please start a new subscription.',
    });
    return;
  }

  res.json({ success: false, message: 'Unable to reactivate subscription.' });
}
```

### Stripe Customer Portal

For a simpler approach to subscription management, Stripe's Customer Portal lets users manage their own subscriptions without custom UI. Configure the portal in your Stripe Dashboard and redirect users to it:

```typescript
// server/routes/portal.ts — Stripe Customer Portal redirect

export async function createPortalSession(
  req: Request,
  res: Response
): Promise<void> {
  const { extensionUserId } = req.body;

  const license = await db.licenses.findUnique({
    where: { extensionUserId },
  });

  if (!license?.stripeCustomerId) {
    res.status(404).json({ error: 'No customer record found' });
    return;
  }

  const session = await stripe.billingPortal.sessions.create({
    customer: license.stripeCustomerId,
    return_url: `${process.env.APP_URL}/account`,
  });

  res.json({ url: session.url });
}
```

---

## Testing with Stripe CLI in Development

The Stripe CLI is essential for local development. It forwards webhook events from Stripe to your local server, letting you test the complete payment flow without deploying.

### Setup

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login to your Stripe account
stripe login

# Forward webhooks to your local server
stripe listen --forward-to localhost:3000/api/webhooks/stripe
```

The CLI prints a webhook signing secret (starting with `whsec_`). Use this as your `STRIPE_WEBHOOK_SECRET` environment variable during local development.

### Triggering Test Events

```bash
# Trigger a checkout session completed event
stripe trigger checkout.session.completed

# Trigger a subscription update
stripe trigger customer.subscription.updated

# Trigger a payment failure
stripe trigger invoice.payment_failed

# Trigger a subscription cancellation
stripe trigger customer.subscription.deleted
```

### Test Card Numbers

Stripe provides test card numbers for various scenarios:

| Card Number | Scenario |
|---|---|
| 4242 4242 4242 4242 | Successful payment |
| 4000 0000 0000 3220 | Requires 3D Secure authentication |
| 4000 0000 0000 9995 | Payment declined (insufficient funds) |
| 4000 0000 0000 0341 | Attaching card fails |
| 4000 0025 0000 3155 | Requires authentication on all transactions |

Use any future expiration date, any 3-digit CVC, and any 5-digit ZIP code with test cards.

### End-to-End Testing Workflow

1. Start your backend server locally.
2. Run `stripe listen --forward-to localhost:3000/api/webhooks/stripe`.
3. Load your extension in Chrome with developer mode.
4. Click "Upgrade" in the extension.
5. Complete checkout using test card `4242 4242 4242 4242`.
6. Verify the webhook arrives in your terminal.
7. Confirm the extension unlocks premium features.
8. Test cancellation, upgrade, and reactivation flows.

### Automated Testing

Write integration tests that use the Stripe test mode API directly:

```typescript
// tests/stripe-integration.test.ts

import Stripe from 'stripe';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY_TEST!, {
  apiVersion: '2024-04-10',
});

describe('Stripe Checkout Integration', () => {
  it('creates a checkout session with correct parameters', async () => {
    const session = await stripe.checkout.sessions.create({
      payment_method_types: ['card'],
      line_items: [{ price: process.env.STRIPE_PRICE_PRO_MONTHLY!, quantity: 1 }],
      mode: 'subscription',
      success_url: 'https://example.com/success',
      cancel_url: 'https://example.com/cancel',
      metadata: { extensionUserId: 'test-user-123' },
    });

    expect(session.id).toBeDefined();
    expect(session.url).toContain('checkout.stripe.com');
    expect(session.mode).toBe('subscription');
  });

  it('handles subscription cancellation', async () => {
    // Create a test subscription first
    const customer = await stripe.customers.create({ email: 'test@example.com' });
    const subscription = await stripe.subscriptions.create({
      customer: customer.id,
      items: [{ price: process.env.STRIPE_PRICE_PRO_MONTHLY! }],
      payment_behavior: 'default_incomplete',
    });

    // Cancel at period end
    const canceled = await stripe.subscriptions.update(subscription.id, {
      cancel_at_period_end: true,
    });

    expect(canceled.cancel_at_period_end).toBe(true);
    expect(canceled.status).toBe('incomplete'); // Test mode won't charge

    // Clean up
    await stripe.subscriptions.cancel(subscription.id);
    await stripe.customers.del(customer.id);
  });
});
```

---

## PCI Compliance for Extensions

Payment Card Industry Data Security Standard (PCI DSS) compliance is mandatory for any business that processes, stores, or transmits credit card data. Chrome extensions that use Stripe Checkout or Stripe Elements benefit from Stripe's PCI compliance, but you must still follow specific practices.

### What Stripe Handles

When you use Stripe Checkout (the hosted payment page) or Stripe Elements (the embeddable card form), Stripe handles all credit card data. Card numbers, CVCs, and expiration dates never touch your servers or your extension. This means you qualify for SAQ A, the simplest PCI compliance level, which requires minimal self-assessment.

### Your Responsibilities

Even with Stripe handling card data, you must:

1. **Never log or store card data**: Ensure your extension code never captures, stores, or transmits credit card information. This includes console.log statements during development that might accidentally capture card fields.

2. **Use HTTPS everywhere**: All communication between your extension, your backend, and Stripe must use HTTPS. Never send any data over unencrypted connections.

3. **Keep your Stripe secret key secure**: Store it in environment variables on your server. Never embed it in your extension code, frontend JavaScript, or version control.

4. **Use Content Security Policy**: Your extension's manifest.json should include a strict CSP that prevents injection of unauthorized scripts. This protects against XSS attacks that could steal payment data.

5. **Keep dependencies updated**: Regularly update the Stripe SDK and all backend dependencies. Security patches are critical for maintaining PCI compliance.

6. **Implement webhook signature verification**: Always verify webhook signatures to prevent spoofed events from modifying subscription data.

### Extension-Specific PCI Considerations

Chrome extensions have unique security properties that affect PCI compliance:

- **Content scripts run in web page context**: Never process payment-related data in content scripts. They share the page's JavaScript environment and could be compromised by malicious websites.
- **Background service workers are isolated**: Payment coordination logic belongs in the service worker, which runs in an isolated context.
- **Popup and options pages are extension pages**: These are safe contexts for displaying pricing and upgrade buttons, but never for collecting card data directly.
- **chrome.storage is not encrypted**: Do not store sensitive tokens or keys in chrome.storage. If you must store a session token, use short-lived tokens that expire within hours.

### Annual Compliance

Complete Stripe's PCI compliance questionnaire annually through your Stripe Dashboard (Settings > Compliance). For most extension businesses using Stripe Checkout, this is a brief self-assessment form (SAQ A) that takes minutes to complete.

---

---

## Technical Resources

Build better extensions with the Chrome Extension Toolkit:

- [webext-storage](https://github.com/theluckystrike/webext-storage): Type-safe chrome.storage wrapper
- [webext-messaging](https://github.com/theluckystrike/webext-messaging): Promise-based message passing
- [webext-permissions](https://github.com/theluckystrike/webext-permissions): Simplified optional host permissions

For code patterns, see the companion [Chrome Extension Guide](https://github.com/theluckystrike/chrome-extension-guide):

- [Authentication Patterns](https://github.com/theluckystrike/chrome-extension-guide/blob/main/docs/patterns/authentication-patterns.md)
- [Feature Flags](https://github.com/theluckystrike/chrome-extension-guide/blob/main/docs/patterns/feature-flags.md)
- [extension-auth-flow](https://github.com/theluckystrike/extension-auth-flow)

All tools and guides are part of the [Zovo](https://zovo.one) ecosystem.
## Related Articles

- [Freemium Model](/articles/freemium-model) - Balance free and paid features to maximize conversion
- [Subscription Model](/articles/subscription-model) - Recurring revenue strategies for extensions
- [Stripe Integration](/articles/stripe-in-extensions) - Complete payment processing guide


---

**Part of the Extension Monetization Playbook by theluckystrike. More at zovo.one.**
