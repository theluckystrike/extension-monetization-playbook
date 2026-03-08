---

layout: default
title: "Chrome Web Store Payments: What Replaced Google's Deprecated API"
description: "Google deprecated Chrome Web Store payments in 2020 with no replacement. Learn the current best practices for accepting payments in Chrome extensions using Stripe and alternatives."
permalink: /articles/chrome-web-store-payments/

---


The Current State of Chrome Web Store Payments

The chrome.payments API was deprecated in 2020. Google has not shipped a replacement. If you are building a paid Chrome extension today, you are on your own for payments. This is not a temporary gap. It has been years and there is no official timeline for anything new.

What the Old System Offered

One-click purchases directly in the Chrome Web Store listing. Google handled all billing, refunds, and customer support for payments. Developers kept 95% of revenue which was a better split than most platforms. Users trusted it because it looked and felt like buying an app on a phone.

But the system was rigid. You could only do one-time purchases or a single subscription tier. No trials, no metered billing, no promotional pricing. You had zero control over the payment experience. It worked but it was narrow.

Why Google Killed It

The honest answer is that extension payments were a rounding error for Google's revenue. Adoption was low because most extensions are free. The system was expensive to maintain relative to what it generated. Google also did not want the liability of processing payments for hundreds of thousands of extensions with varying quality and trustworthiness.

The deprecation was quiet. Almost like Google hoped nobody would notice. There was no announcement blog post, no developer summit discussion, no roadmap update. One day the docs had a deprecation notice and that was it.

What Replaced It

Nothing official. The developer community independently converged on external payment solutions.

Stripe is the most popular choice for developers who want control. You handle everything from checkout to customer emails to refunds. The developer experience is solid and the fees are reasonable. The tradeoff is you build more infrastructure yourself.

PayPal works but the developer experience is worse. The integration is clunkier and the checkout flow feels dated. Some users still prefer it so it is worth supporting as a secondary option.

Paddle and LemonSqueezy handle more of the complexity including tax compliance and international billing. They are popular with solo developers who do not want to deal with VAT and sales tax calculations. They take a larger cut but save you significant administrative work.

Gumroad works for simple digital product sales. It is the easiest to set up but takes a larger percentage of each sale. Fine for selling a single extension, painful if you are building a business with multiple products.

Each option has tradeoffs in fees, features, and how much infrastructure you need to run yourself. There is no perfect solution.

Migration Timeline

Understanding the key dates helps put the current situation in context and explains why developers had to scramble to find alternatives.

**September 2020**: Google quietly deprecated the chrome.payments API with a minimal notice in the Chrome Web Store documentation. The API continued to function for existing users but no new integrations were possible.

**Early 2021**: The chrome.payments API stopped processing new transactions. Developers who relied on it were forced to migrate immediately or lose revenue. This caught many extension developers off guard since there was no formal announcement.

**2021-2022**: The developer community began converging on Stripe as the de facto standard. LemonSqueezy launched during this period specifically targeting the Chrome extension market. Paddle saw increased adoption among existing SaaS developers expanding into extensions.

**2023-Present**: No official word from Google about any replacement. The Chrome team has acknowledged the gap in developer surveys but no concrete plans have been announced. Developers have fully adapted by building their own payment infrastructure.

The lesson: do not expect Google to fill this gap. The external payment ecosystem is mature enough that even if Google announced something tomorrow, the migration cost would likely not be worth it for most developers.

Stripe vs Paddle vs LemonSqueezy

Choosing the right payment provider depends on your technical capacity, volume, and willingness to handle tax compliance. Here is a practical comparison:

| Feature | Stripe | Paddle | LemonSqueezy |
|---------|--------|--------|--------------|
| Transaction Fees | 1.4% + 25¢ (EU) | 5% + 50¢ | 5% + 50¢ |
| Setup Complexity | Medium | Low | Low |
| Tax Compliance | Stripe Tax (extra) | Built-in | Built-in |
| Subscription Management | Full control | Good | Good |
| Developer Experience | Excellent | Good | Good |
| Extension-Specific Support | Community-driven | Some | Growing |
| Payment Method Control | Full | Partial | Partial |
| Refund Handling | Manual/API | Via platform | Via platform |

Stripe gives you the most control but requires more setup. You need to handle tax calculations yourself unless you enable Stripe Tax. The [Stripe integration for extensions](/articles/stripe-in-extensions/) provides detailed implementation guidance.

Paddle and LemonSqueezy handle VAT, sales tax, and global billing out of the box. This saves significant administrative work especially if you sell internationally. The trade-off is a higher per-transaction fee and less control over the checkout experience.

For most extension developers, LemonSqueezy offers the best balance. The 5% fee includes tax handling which would cost extra with Stripe. Paddle is a solid alternative if you need specific features or have existing integration.

Handling Existing CWS Payment Users

If you had paying users through the Chrome Web Store payments system before deprecation, you faced a difficult migration. Here is what worked for developers in this situation:

**Communicate Early and Often**: Reach out to existing customers before their access expires. Explain the situation honestly. Users who paid for your extension deserve respect and transparency.

**Offer Migration Paths**: Many developers offered existing CWS purchasers a free or discounted license for the new payment system. This acknowledges their loyalty and reduces churn.

**Honor Existing Purchases**: Consider honoring lifetime access for users who bought one-time licenses. You can implement this through license key validation that recognizes legacy purchase patterns.

**Provide Clear Instructions**: Walk users through how to claim their new license. Create a simple form where they enter their original purchase email and receive access to the new system.

**Data Migration**: If you have access to purchase records from the CWS period, use those emails to link accounts. If not, rely on honor systems or manual verification for legacy users.

The key principle: your existing customers trusted you enough to pay. Do not abandon that trust during migration. The short-term cost of honoring legacy purchases builds long-term loyalty that pays dividends.

Current Best Practices for Paid Extensions

Set up Stripe Checkout or a similar hosted payment page. Do not try to build your own payment form unless you have specific requirements that hosted checkout cannot meet.

Build a simple landing page for your extension that explains what the paid version offers. Show the difference between free and paid clearly. Include screenshots and a clear price. This page is where you send users when they click upgrade in your extension.

Link from the extension to the landing page or directly to checkout. A button in the extension UI that opens your website in a new tab is the standard approach. Some developers use a popup within the extension but that adds complexity.

After payment, validate the user via license key or account-based system. License keys are simpler but harder to manage if users have multiple devices. Account-based systems let users sign in and manage their subscription but require more infrastructure. Choose based on how your users work.

Keep the free version genuinely useful so users trust you before paying. The worst paid extensions are ones where the free version does almost nothing. Build something worth paying for.

For implementing [subscription models](/articles/subscription-model/) or [one-time purchases](/articles/one-time-purchase/), refer to those guides for detailed patterns specific to Chrome extensions.

Chrome Web Store Listing Considerations

You can link to your website from the extension listing. Use this to point users to your landing page or pricing information.

Explain pricing clearly in the description so users know before installing. Nothing frustrates users more than installing an extension and then discovering it costs money for features they expected to be free. Be upfront.

Be transparent about what is free and what requires payment. Separate the features clearly in your marketing copy. Users appreciate honesty and it reduces refund requests and negative reviews.

Google allows linking to external payment pages but frowns on dark patterns or confusing upgrade flows. Keep it clean and honest. Do not trick users into upgrading. Do not hide cancel buttons. Do not use manipulative language.

For Manifest V3 payment integration patterns, check the [Chrome Extension Guide](/docs/chrome-extension-guide/) for technical implementation details specific to the current extension architecture.

What Might Come Next

Google has occasionally hinted at revisiting extension payments or building new commerce APIs but nothing has shipped. The hints come up in developer surveys and occasional comments from Chrome team members but they never materialize into anything concrete.

The Payment Request API exists for web pages but is not available in extension contexts in a useful way. You cannot use it to process payments inside an extension today.

Do not wait for Google to solve this. Build your own payment stack now and if Google ever ships something, evaluate it then. You will almost certainly want to keep your own system anyway for the flexibility. The control you gain over your billing is worth the effort.

How zovo.one Handled This

zovo.one built its entire payment infrastructure independently using Stripe after the CWS payments deprecation. The team evaluated the external payment options, chose Stripe for its flexibility and developer experience, and implemented license key-based validation across their extension suite.

Having full control over billing turned out to be an advantage rather than a burden. They run 17 extensions with various pricing models including one-time purchases, subscriptions, and tiered plans. Each has its own checkout flow, its own pricing page, and its own customer communication system.

The initial setup took more time than using a built-in system would have but the long-term benefits outweigh the cost. They own their customer data, they control the upgrade experience, and they keep more revenue than they would have with any third-party platform that handles payments for them.

If you are starting today, the same path is available to you. Pick your payment provider, build your landing page, implement license validation, and ship. The gap left by Google is real but it is also an opportunity to own your business completely.

---

## Related Articles

- [Stripe In Extensions](articles/stripe-in-extensions.md)
- [Handling Refunds](articles/handling-refunds.md)
- [License Key System](articles/license-key-system.md)


---

Part of the Extension Monetization Playbook by theluckystrike. Professional Chrome extension development at zovo.one


## Related Articles

- [Server Side Validation](articles/server-side-validation/)
- [Selling Your Extension](articles/selling-your-extension/)
- [One Time Purchase](articles/one-time-purchase/)



---

Part of the Extension Monetization Playbook by theluckystrike. Chrome extension development services at zovo.one.
