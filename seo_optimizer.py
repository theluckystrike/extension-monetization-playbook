#!/usr/bin/env python3
"""
Script to add SEO front matter, footer, and related articles to all .md files.
"""

import os
import re
from pathlib import Path

# Define all markdown files
MD_FILES = [
    "./articles/affiliate-model.md",
    "./articles/analytics-without-tracking.md",
    "./articles/belikenative-case-study.md",
    "./articles/case-studies-overview.md",
    "./articles/chrome-web-store-payments.md",
    "./articles/chrome-web-store-seo.md",
    "./articles/community-building.md",
    "./articles/content-marketing.md",
    "./articles/cross-promotion.md",
    "./articles/extension-as-a-service.md",
    "./articles/extension-valuation.md",
    "./articles/failed-experiments.md",
    "./articles/freemium-model.md",
    "./articles/growth-playbook-overview.md",
    "./articles/handling-refunds.md",
    "./articles/legal-essentials.md",
    "./articles/license-key-system.md",
    "./articles/monetization-strategies-overview.md",
    "./articles/one-time-purchase.md",
    "./articles/payment-integration-overview.md",
    "./articles/paywall-patterns.md",
    "./articles/pricing-strategies.md",
    "./articles/review-acquisition.md",
    "./articles/scaling-solo.md",
    "./articles/selling-your-extension.md",
    "./articles/server-side-validation.md",
    "./articles/sponsorship-model.md",
    "./articles/stripe-in-extensions.md",
    "./articles/subscription-model.md",
    "./articles/tab-suspender-pro-case-study.md",
    "./articles/technical-implementation-links.md",
    "./articles/trial-implementation.md",
    "./articles/update-monetization.md",
    "./articles/zero-to-1000-users.md",
    "./articles/zovo-bundle-case-study.md",
    "./CONTRIBUTING.md",
    "./docs/analytics/extension-analytics-complete-guide.md",
    "./docs/case-studies/successful-extension-businesses.md",
    "./docs/getting-started/introduction.md",
    "./docs/growth/chrome-web-store-seo.md",
    "./docs/growth/zero-to-1000-users.md",
    "./docs/payments/paypal-integration-extensions.md",
    "./docs/payments/stripe-in-extensions.md",
    "./docs/revenue/freemium-model.md",
    "./docs/revenue/in-app-purchases-extensions.md",
    "./docs/technical-guides-index.md",
    "./index.md",
    "./README.md",
    "./resources/improved-readmes/webext-dns.md",
]

# Define related articles for each file (3 related articles)
RELATED_ARTICLES = {
    "./articles/affiliate-model.md": [
        "./articles/sponsorship-model.md",
        "./articles/monetization-strategies-overview.md",
        "./articles/content-marketing.md"
    ],
    "./articles/analytics-without-tracking.md": [
        "./articles/stripe-in-extensions.md",
        "./articles/server-side-validation.md",
        "./articles/legal-essentials.md"
    ],
    "./articles/belikenative-case-study.md": [
        "./articles/zovo-bundle-case-study.md",
        "./articles/tab-suspender-pro-case-study.md",
        "./articles/monetization-strategies-overview.md"
    ],
    "./articles/case-studies-overview.md": [
        "./articles/zovo-bundle-case-study.md",
        "./articles/tab-suspender-pro-case-study.md",
        "./articles/belikenative-case-study.md"
    ],
    "./articles/chrome-web-store-payments.md": [
        "./articles/stripe-in-extensions.md",
        "./articles/payment-integration-overview.md",
        "./articles/license-key-system.md"
    ],
    "./articles/chrome-web-store-seo.md": [
        "./articles/zero-to-1000-users.md",
        "./articles/content-marketing.md",
        "./articles/growth-playbook-overview.md"
    ],
    "./articles/community-building.md": [
        "./articles/content-marketing.md",
        "./articles/cross-promotion.md",
        "./articles/scaling-solo.md"
    ],
    "./articles/content-marketing.md": [
        "./articles/chrome-web-store-seo.md",
        "./articles/zero-to-1000-users.md",
        "./articles/growth-playbook-overview.md"
    ],
    "./articles/cross-promotion.md": [
        "./articles/chrome-web-store-seo.md",
        "./articles/community-building.md",
        "./articles/content-marketing.md"
    ],
    "./articles/extension-as-a-service.md": [
        "./articles/subscription-model.md",
        "./articles/freemium-model.md",
        "./articles/monetization-strategies-overview.md"
    ],
    "./articles/extension-valuation.md": [
        "./articles/selling-your-extension.md",
        "./articles/monetization-strategies-overview.md",
        "./articles/pricing-strategies.md"
    ],
    "./articles/failed-experiments.md": [
        "./articles/pricing-strategies.md",
        "./articles/monetization-strategies-overview.md",
        "./articles/freemium-model.md"
    ],
    "./articles/freemium-model.md": [
        "./articles/subscription-model.md",
        "./articles/paywall-patterns.md",
        "./articles/pricing-strategies.md"
    ],
    "./articles/growth-playbook-overview.md": [
        "./articles/zero-to-1000-users.md",
        "./articles/chrome-web-store-seo.md",
        "./articles/content-marketing.md"
    ],
    "./articles/handling-refunds.md": [
        "./articles/legal-essentials.md",
        "./articles/stripe-in-extensions.md",
        "./articles/payment-integration-overview.md"
    ],
    "./articles/legal-essentials.md": [
        "./articles/license-key-system.md",
        "./articles/handling-refunds.md",
        "./articles/server-side-validation.md"
    ],
    "./articles/license-key-system.md": [
        "./articles/server-side-validation.md",
        "./articles/stripe-in-extensions.md",
        "./articles/payment-integration-overview.md"
    ],
    "./articles/monetization-strategies-overview.md": [
        "./articles/subscription-model.md",
        "./articles/freemium-model.md",
        "./articles/pricing-strategies.md"
    ],
    "./articles/one-time-purchase.md": [
        "./articles/subscription-model.md",
        "./articles/freemium-model.md",
        "./articles/pricing-strategies.md"
    ],
    "./articles/payment-integration-overview.md": [
        "./articles/stripe-in-extensions.md",
        "./articles/license-key-system.md",
        "./articles/paywall-patterns.md"
    ],
    "./articles/paywall-patterns.md": [
        "./articles/freemium-model.md",
        "./articles/trial-implementation.md",
        "./articles/subscription-model.md"
    ],
    "./articles/pricing-strategies.md": [
        "./articles/subscription-model.md",
        "./articles/freemium-model.md",
        "./articles/one-time-purchase.md"
    ],
    "./articles/review-acquisition.md": [
        "./articles/chrome-web-store-seo.md",
        "./articles/zero-to-1000-users.md",
        "./articles/growth-playbook-overview.md"
    ],
    "./articles/scaling-solo.md": [
        "./articles/selling-your-extension.md",
        "./articles/extension-valuation.md",
        "./articles/community-building.md"
    ],
    "./articles/selling-your-extension.md": [
        "./articles/extension-valuation.md",
        "./articles/scaling-solo.md",
        "./articles/monetization-strategies-overview.md"
    ],
    "./articles/server-side-validation.md": [
        "./articles/license-key-system.md",
        "./articles/stripe-in-extensions.md",
        "./articles/legal-essentials.md"
    ],
    "./articles/sponsorship-model.md": [
        "./articles/affiliate-model.md",
        "./articles/monetization-strategies-overview.md",
        "./articles/content-marketing.md"
    ],
    "./articles/stripe-in-extensions.md": [
        "./articles/payment-integration-overview.md",
        "./articles/license-key-system.md",
        "./articles/server-side-validation.md"
    ],
    "./articles/subscription-model.md": [
        "./articles/freemium-model.md",
        "./articles/pricing-strategies.md",
        "./articles/monetization-strategies-overview.md"
    ],
    "./articles/tab-suspender-pro-case-study.md": [
        "./articles/zovo-bundle-case-study.md",
        "./articles/belikenative-case-study.md",
        "./articles/case-studies-overview.md"
    ],
    "./articles/technical-implementation-links.md": [
        "./articles/payment-integration-overview.md",
        "./articles/monetization-strategies-overview.md",
        "./articles/server-side-validation.md"
    ],
    "./articles/trial-implementation.md": [
        "./articles/paywall-patterns.md",
        "./articles/freemium-model.md",
        "./articles/subscription-model.md"
    ],
    "./articles/update-monetization.md": [
        "./articles/monetization-strategies-overview.md",
        "./articles/pricing-strategies.md",
        "./articles/paywall-patterns.md"
    ],
    "./articles/zero-to-1000-users.md": [
        "./articles/growth-playbook-overview.md",
        "./articles/chrome-web-store-seo.md",
        "./articles/content-marketing.md"
    ],
    "./articles/zovo-bundle-case-study.md": [
        "./articles/tab-suspender-pro-case-study.md",
        "./articles/belikenative-case-study.md",
        "./articles/case-studies-overview.md"
    ],
    "./CONTRIBUTING.md": [
        "./articles/monetization-strategies-overview.md",
        "./articles/technical-implementation-links.md",
        "./index.md"
    ],
    "./docs/analytics/extension-analytics-complete-guide.md": [
        "./articles/analytics-without-tracking.md",
        "./articles/stripe-in-extensions.md",
        "./articles/server-side-validation.md"
    ],
    "./docs/case-studies/successful-extension-businesses.md": [
        "./articles/zovo-bundle-case-study.md",
        "./articles/tab-suspender-pro-case-study.md",
        "./articles/case-studies-overview.md"
    ],
    "./docs/getting-started/introduction.md": [
        "./articles/monetization-strategies-overview.md",
        "./articles/pricing-strategies.md",
        "./articles/freemium-model.md"
    ],
    "./docs/growth/chrome-web-store-seo.md": [
        "./articles/chrome-web-store-seo.md",
        "./articles/zero-to-1000-users.md",
        "./articles/content-marketing.md"
    ],
    "./docs/growth/zero-to-1000-users.md": [
        "./articles/zero-to-1000-users.md",
        "./articles/growth-playbook-overview.md",
        "./articles/chrome-web-store-seo.md"
    ],
    "./docs/payments/paypal-integration-extensions.md": [
        "./articles/stripe-in-extensions.md",
        "./articles/chrome-web-store-payments.md",
        "./articles/payment-integration-overview.md"
    ],
    "./docs/payments/stripe-in-extensions.md": [
        "./articles/stripe-in-extensions.md",
        "./articles/payment-integration-overview.md",
        "./articles/license-key-system.md"
    ],
    "./docs/revenue/freemium-model.md": [
        "./articles/freemium-model.md",
        "./articles/subscription-model.md",
        "./articles/paywall-patterns.md"
    ],
    "./docs/revenue/in-app-purchases-extensions.md": [
        "./articles/chrome-web-store-payments.md",
        "./articles/stripe-in-extensions.md",
        "./articles/payment-integration-overview.md"
    ],
    "./docs/technical-guides-index.md": [
        "./articles/technical-implementation-links.md",
        "./articles/payment-integration-overview.md",
        "./articles/monetization-strategies-overview.md"
    ],
    "./index.md": [
        "./articles/monetization-strategies-overview.md",
        "./articles/pricing-strategies.md",
        "./articles/zero-to-1000-users.md"
    ],
    "./README.md": [
        "./articles/monetization-strategies-overview.md",
        "./articles/pricing-strategies.md",
        "./index.md"
    ],
    "./resources/improved-readmes/webext-dns.md": [
        "./articles/server-side-validation.md",
        "./articles/technical-implementation-links.md",
        "./docs/technical-guides-index.md"
    ],
}

# SEO titles and descriptions for each file
SEO_DATA = {
    "./articles/affiliate-model.md": {
        "title": "Chrome Extension Affiliate Marketing: Monetize Without Payments",
        "description": "Learn how to earn affiliate revenue from your Chrome extension. Best programs, implementation tips, and how to avoid alienating users."
    },
    "./articles/analytics-without-tracking.md": {
        "title": "Privacy-First Analytics for Chrome Extensions: Complete Guide",
        "description": "Track essential metrics without tracking users. Privacy-compliant analytics solutions for Chrome extensions that respect user data."
    },
    "./articles/belikenative-case-study.md": {
        "title": "BeLikeNative Case Study: Language Extension Revenue",
        "description": "How BeLikeNative built a profitable Chrome extension for language learners. Real revenue numbers and growth strategies."
    },
    "./articles/case-studies-overview.md": {
        "title": "Chrome Extension Case Studies: Real Revenue Data",
        "description": "In-depth case studies of successful Chrome extensions. Revenue, growth tactics, and lessons from developers making $10K+/month."
    },
    "./articles/chrome-web-store-payments.md": {
        "title": "Chrome Extension Payments 2026: Best Payment Processors",
        "description": "Google deprecated Chrome Web Store payments. Learn the best alternatives for accepting payments in Chrome extensions today."
    },
    "./articles/chrome-web-store-seo.md": {
        "title": "Chrome Web Store SEO: How to Rank Higher in 2026",
        "description": "Master Chrome Web Store SEO to get more installs. Keyword optimization, screenshot best practices, and ranking factors that work."
    },
    "./articles/community-building.md": {
        "title": "Build a Community Around Your Chrome Extension",
        "description": "Create a loyal user community that becomes your competitive advantage. Where to build, how to grow, and monetization benefits."
    },
    "./articles/content-marketing.md": {
        "title": "Content Marketing for Chrome Extensions: Growth Guide",
        "description": "Drive organic traffic to your Chrome extension with content marketing. What to write, where to publish, and conversion tactics."
    },
    "./articles/cross-promotion.md": {
        "title": "Cross-Promote Chrome Extensions: Grow Your User Base",
        "description": "Proven cross-promotion strategies for Chrome extension developers. Leverage existing audiences to gain more users."
    },
    "./articles/extension-as-a-service.md": {
        "title": "Chrome Extension as a Service: SaaS Business Model",
        "description": "Turn your Chrome extension into a SaaS business. Architecture patterns, pricing strategies, and hybrid monetization approaches."
    },
    "./articles/extension-valuation.md": {
        "title": "How to Value a Chrome Extension Business",
        "description": "Calculate what your Chrome extension is worth. Revenue multiples, growth rates, and factors that increase sale value."
    },
    "./articles/failed-experiments.md": {
        "title": "Failed Chrome Extension Monetization Experiments",
        "description": "Real data from monetization strategies that didn't work. Learn what not to do when monetizing your extension."
    },
    "./articles/freemium-model.md": {
        "title": "Freemium Model for Chrome Extensions: Complete Guide",
        "description": "Master the freemium model for Chrome extensions. Feature gating, conversion optimization, and implementation with code examples."
    },
    "./articles/growth-playbook-overview.md": {
        "title": "Chrome Extension Growth Playbook: 0 to 10K Users",
        "description": "Proven tactics to grow your Chrome extension from launch to 10,000 users. SEO, content marketing, and community building."
    },
    "./articles/handling-refunds.md": {
        "title": "Chrome Extension Refund Policy: Best Practices",
        "description": "Create a refund policy that builds trust and prevents chargebacks. Stripe integration and handling common refund scenarios."
    },
    "./articles/legal-essentials.md": {
        "title": "Legal Essentials for Chrome Extension Developers",
        "description": "Privacy policies, terms of service, GDPR compliance, and business structure for Chrome extension developers who monetize."
    },
    "./articles/license-key-system.md": {
        "title": "License Key System for Chrome Extensions",
        "description": "Build a robust license key system for your Chrome extension. Key generation, validation, activation limits, and anti-piracy."
    },
    "./articles/monetization-strategies-overview.md": {
        "title": "Chrome Extension Monetization Strategies: Complete Guide",
        "description": "Every proven way to make money from Chrome extensions in 2026. Freemium, subscriptions, one-time purchases, and more."
    },
    "./articles/one-time-purchase.md": {
        "title": "One-Time Purchase for Chrome Extensions: Lifetime Pricing",
        "description": "When to use one-time pricing for Chrome extensions. Find the pricing sweet spot and generate ongoing revenue from single sales."
    },
    "./articles/payment-integration-overview.md": {
        "title": "Chrome Extension Payment Integration: Complete Guide",
        "description": "How to accept payments in Chrome extensions. Stripe, license keys, server validation, and paywall patterns explained."
    },
    "./articles/paywall-patterns.md": {
        "title": "Paywall Patterns for Chrome Extensions That Convert",
        "description": "Design effective paywalls for browser extensions. Modal design, UX strategies, and patterns that maximize conversions."
    },
    "./articles/pricing-strategies.md": {
        "title": "Chrome Extension Pricing Strategies: Data-Driven Guide",
        "description": "How to price your Chrome extension for maximum revenue. Price anchoring, A/B testing, and psychological pricing tactics."
    },
    "./articles/review-acquisition.md": {
        "title": "Get More Chrome Extension Reviews: Ethical Strategies",
        "description": "Proven strategies to increase Chrome Web Store reviews. Timing, prompts, and psychology to earn authentic 5-star reviews."
    },
    "./articles/scaling-solo.md": {
        "title": "Scale Your Chrome Extension Business Solo",
        "description": "How one developer built a 17-extension portfolio with 4,000+ users. Systems for automation, support, and portfolio management."
    },
    "./articles/selling-your-extension.md": {
        "title": "How to Sell Your Chrome Extension: Complete Guide",
        "description": "Learn when and how to sell your Chrome extension. Where to list it, how to transfer ownership, and structure deals."
    },
    "./articles/server-side-validation.md": {
        "title": "Server-Side License Validation for Chrome Extensions",
        "description": "Build secure server-side license validation. API design, caching strategies, offline support, and replay attack prevention."
    },
    "./articles/sponsorship-model.md": {
        "title": "Chrome Extension Sponsorship: Find and Land Sponsors",
        "description": "Monetize your Chrome extension through sponsorships. How to find sponsors, price deals, and maintain user trust."
    },
    "./articles/stripe-in-extensions.md": {
        "title": "Stripe Integration for Chrome Extensions: Tutorial",
        "description": "Step-by-step guide to integrating Stripe payments in Chrome extensions. Backend setup, webhooks, and license management."
    },
    "./articles/subscription-model.md": {
        "title": "Subscription Pricing for Chrome Extensions: Complete Guide",
        "description": "How to implement subscription pricing for Chrome extensions. Monthly vs annual, churn reduction, and Stripe integration."
    },
    "./articles/tab-suspender-pro-case-study.md": {
        "title": "Tab Suspender Pro Case Study: Competing in Crowded Markets",
        "description": "How Tab Suspender Pro competes with millions of users in the tab management space. Trust, performance, and differentiation."
    },
    "./articles/technical-implementation-links.md": {
        "title": "Chrome Extension Monetization: Technical Implementation",
        "description": "Technical reference linking every monetization strategy to implementation guides. Payment integration, licensing, and templates."
    },
    "./articles/trial-implementation.md": {
        "title": "Free Trial Implementation for Chrome Extensions",
        "description": "Build time-limited and feature-limited trials for Chrome extensions. Trial architecture, tamper prevention, and conversion."
    },
    "./articles/update-monetization.md": {
        "title": "Monetize Chrome Extension Updates: Paid Upgrades",
        "description": "How to monetize major Chrome extension updates. Paid upgrade paths, version-based licensing, and communicating value."
    },
    "./articles/zero-to-1000-users.md": {
        "title": "Zero to 1,000 Users: Chrome Extension Launch Playbook",
        "description": "Complete launch playbook for Chrome extensions. Marketing channels, community building, and retention strategies."
    },
    "./articles/zovo-bundle-case-study.md": {
        "title": "Zovo Bundle Case Study: How Bundling 17 Extensions Works",
        "description": "How the Zovo extension bundle generates $40K/month through bundling. Strategy, pricing, and technical implementation."
    },
    "./CONTRIBUTING.md": {
        "title": "Contribute to the Extension Monetization Playbook",
        "description": "Learn how to contribute to the Extension Monetization Playbook. Add new articles, improve content, or report errors."
    },
    "./docs/analytics/extension-analytics-complete-guide.md": {
        "title": "Complete Guide to Chrome Extension Analytics",
        "description": "Implement analytics in Chrome extensions with GA4, Mixpanel, and custom solutions. Privacy-compliant tracking and key metrics."
    },
    "./docs/case-studies/successful-extension-businesses.md": {
        "title": "10 Chrome Extensions Making $10K+/Month",
        "description": "Deep analysis of 10 real Chrome extension businesses generating $10,000+ monthly. Revenue models and growth strategies."
    },
    "./docs/getting-started/introduction.md": {
        "title": "Getting Started with Chrome Extension Monetization",
        "description": "Welcome to the Extension Monetization Playbook! Learn how to monetize your browser extension effectively."
    },
    "./docs/growth/chrome-web-store-seo.md": {
        "title": "Chrome Web Store SEO: Complete Ranking Guide",
        "description": "Master Chrome Web Store SEO with ranking factors, keyword research, localization, and screenshot optimization."
    },
    "./docs/growth/zero-to-1000-users.md": {
        "title": "Zero to 1,000 Users: Chrome Extension Launch",
        "description": "Complete launch playbook for Chrome extensions. Marketing channels, community building, and retention strategies."
    },
    "./docs/payments/paypal-integration-extensions.md": {
        "title": "PayPal Integration for Chrome Extensions: Developer Guide",
        "description": "Complete guide to integrating PayPal in Chrome extensions. Checkout flows, webhooks, and license validation."
    },
    "./docs/payments/stripe-in-extensions.md": {
        "title": "Stripe Integration for Chrome Extensions: TypeScript Guide",
        "description": "Complete guide to integrating Stripe in Chrome extensions. Checkout sessions, webhooks, and subscription management."
    },
    "./docs/revenue/freemium-model.md": {
        "title": "Freemium Model for Chrome Extensions: Conversion Guide",
        "description": "Master the freemium model for browser extensions. Detailed conversion funnels, feature gating code, and pricing psychology."
    },
    "./docs/revenue/in-app-purchases-extensions.md": {
        "title": "In-App Purchases for Chrome Extensions: Implementation Guide",
        "description": "Master in-app purchases for Chrome extensions. Chrome Web Store Payments, digital goods, and premium feature gating."
    },
    "./docs/technical-guides-index.md": {
        "title": "Chrome Extension Monetization: Technical Guides",
        "description": "Technical guides for Chrome extension monetization. Payment integration, licensing, analytics, and starter templates."
    },
    "./index.md": {
        "title": "Chrome Extension Monetization Playbook",
        "description": "Complete guide to monetizing Chrome extensions - revenue models, payments, growth strategies, and case studies."
    },
    "./README.md": {
        "title": "Extension Monetization Playbook: Make Money from Chrome Extensions",
        "description": "A实战指南 for monetizing browser extensions effectively. Proven strategies from real-world case studies."
    },
    "./resources/improved-readmes/webext-dns.md": {
        "title": "Chrome Extension DNS API: TypeScript Wrapper Guide",
        "description": "TypeScript wrapper for Chrome DNS API. Clean interface for DNS resolution in Chrome extensions with code examples."
    },
}

FOOTER = """

---

*Part of the Extension Monetization Playbook by theluckystrike. Chrome extension development services at [zovo.one](https://zovo.one).*
"""

def process_file(filepath):
    """Process a single markdown file."""
    filepath = Path(filepath)
    
    if not filepath.exists():
        print(f"  [SKIP] File not found: {filepath}")
        return False
    
    content = filepath.read_text(encoding='utf-8')
    
    # Check if front matter already exists
    has_front_matter = content.startswith('---')
    
    # Get SEO data for this file
    seo_key = str(filepath)
    if seo_key not in SEO_DATA:
        # Try without leading ./
        seo_key = "./" + str(filepath)
    
    seo_info = SEO_DATA.get(seo_key, {
        "title": "Chrome Extension Monetization Guide",
        "description": "Learn how to monetize your Chrome extension effectively."
    })
    
    # Verify description is under 160 chars
    if len(seo_info["description"]) >= 160:
        print(f"  [WARNING] Description too long for {filepath}: {len(seo_info['description'])} chars")
    
    # Build front matter
    new_front_matter = f"""---
layout: default
title: "{seo_info['title']}"
description: "{seo_info['description']}"
---
"""
    
    if has_front_matter:
        # Find the end of front matter
        parts = content.split('---', 2)
        if len(parts) >= 3:
            # Keep existing front matter but ensure it has layout: default
            existing_fm = parts[1]
            existing_content = parts[2]
            
            # Check if layout: default exists
            if 'layout:' not in existing_fm:
                # Add layout after the first line that has content
                lines = existing_fm.split('\n')
                new_lines = []
                for line in lines:
                    new_lines.append(line)
                    if line.strip() and not line.strip().startswith('#'):
                        # Insert layout: default after first key-value pair
                        new_lines.insert(-1, 'layout: default')
                        break
                existing_fm = '\n'.join(new_lines)
            elif 'layout: default' not in existing_fm and 'layout:article' in existing_fm:
                # Replace layout: article with layout: default
                existing_fm = existing_fm.replace('layout: article', 'layout: default')
            
            # Update or add title and description if missing
            if 'title:' not in existing_fm:
                existing_fm = existing_fm.strip() + f'\ntitle: "{seo_info["title"]}"'
            if 'description:' not in existing_fm:
                existing_fm = existing_fm.strip() + f'\ndescription: "{seo_info["description"]}"'
            
            # Reconstruct content
            content = f"---\n{existing_fm}\n---\n{existing_content}"
            print(f"  [UPDATE] Updated front matter: {filepath}")
        else:
            # Malformed front matter - prepend new one
            content = new_front_matter + content
            print(f"  [UPDATE] Replaced malformed front matter: {filepath}")
    else:
        # No front matter - prepend new one
        content = new_front_matter + content
        print(f"  [ADD] Added front matter: {filepath}")
    
    # Add footer if not already present
    footer_present = "Part of the Extension Monetization Playbook" in content
    if not footer_present:
        content = content.rstrip() + FOOTER
        print(f"  [ADD] Added footer: {filepath}")
    else:
        print(f"  [SKIP] Footer already present: {filepath}")
    
    # Add Related Articles section
    related_key = str(filepath)
    if related_key not in RELATED_ARTICLES:
        related_key = "./" + str(filepath)
    
    related_articles = RELATED_ARTICLES.get(related_key, [])
    
    if related_articles:
        # Convert file paths to article titles
        related_links = []
        for article_path in related_articles:
            article_name = Path(article_path).stem
            # Convert hyphen-case to Title Case
            title_name = article_name.replace('-', ' ').title()
            # Create relative path
            if article_path.startswith('./'):
                article_path = article_path[2:]
            related_links.append(f"- [{title_name}]({article_path})")
        
        related_section = f"""

## Related Articles

{chr(10).join(related_links)}
"""
        
        # Check if Related Articles section already exists
        if '## Related Articles' not in content:
            content = content.rstrip() + related_section
            print(f"  [ADD] Added related articles: {filepath}")
        else:
            print(f"  [SKIP] Related articles already present: {filepath}")
    
    # Write the updated content
    filepath.write_text(content, encoding='utf-8')
    return True


def main():
    print("Processing markdown files for SEO optimization...")
    print("=" * 60)
    
    success_count = 0
    for md_file in MD_FILES:
        print(f"\nProcessing: {md_file}")
        if process_file(md_file):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"Completed! Processed {success_count}/{len(MD_FILES)} files successfully.")


if __name__ == "__main__":
    main()
