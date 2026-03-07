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

Current Best Practices for Paid Extensions

Set up Stripe Checkout or a similar hosted payment page. Do not try to build your own payment form unless you have specific requirements that hosted checkout cannot meet.

Build a simple landing page for your extension that explains what the paid version offers. Show the difference between free and paid clearly. Include screenshots and a clear price. This page is where you send users when they click upgrade in your extension.

Link from the extension to the landing page or directly to checkout. A button in the extension UI that opens your website in a new tab is the standard approach. Some developers use a popup within the extension but that adds complexity.

After payment, validate the user via license key or account-based system. License keys are simpler but harder to manage if users have multiple devices. Account-based systems let users sign in and manage their subscription but require more infrastructure. Choose based on how your users work.

Keep the free version genuinely useful so users trust you before paying. The worst paid extensions are ones where the free version does almost nothing. Build something worth paying for.

Chrome Web Store Listing Considerations

You can link to your website from the extension listing. Use this to point users to your landing page or pricing information.

Explain pricing clearly in the description so users know before installing. Nothing frustrates users more than installing an extension and then discovering it costs money for features they expected to be free. Be upfront.

Be transparent about what is free and what requires payment. Separate the features clearly in your marketing copy. Users appreciate honesty and it reduces refund requests and negative reviews.

Google allows linking to external payment pages but frowns on dark patterns or confusing upgrade flows. Keep it clean and honest. Do not trick users into upgrading. Do not hide cancel buttons. Do not use manipulative language.

What Might Come Next

Google has occasionally hinted at revisiting extension payments or building new commerce APIs but nothing has shipped. The hints come up in developer surveys and occasional comments from Chrome team members but they never materialize into anything concrete.

The Payment Request API exists for web pages but is not available in extension contexts in a useful way. You cannot use it to process payments inside an extension today.

Do not wait for Google to solve this. Build your own payment stack now and if Google ever ships something, evaluate it then. You will almost certainly want to keep your own system anyway for the flexibility. The control you gain over your billing is worth the effort.

How zovo.one Handled This

zovo.one built its entire payment infrastructure independently using Stripe after the CWS payments deprecation. The team evaluated the external payment options, chose Stripe for its flexibility and developer experience, and implemented license key-based validation across their extension suite.

Having full control over billing turned out to be an advantage rather than a burden. They run 17 extensions with various pricing models including one-time purchases, subscriptions, and tiered plans. Each has its own checkout flow, its own pricing page, and its own customer communication system.

The initial setup took more time than using a built-in system would have but the long-term benefits outweigh the cost. They own their customer data, they control the upgrade experience, and they keep more revenue than they would have with any third-party platform that handles payments for them.

If you are starting today, the same path is available to you. Pick your payment provider, build your landing page, implement license validation, and ship. The gap left by Google is real but it is also an opportunity to own your business completely.
