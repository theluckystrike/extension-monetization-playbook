#!/usr/bin/env python3
"""
Script to add Jekyll front matter, footer, and related articles to all .md files.
"""

import os
import re
from pathlib import Path

# Define the footer to add to each article
FOOTER = """

---

Part of the Extension Monetization Playbook by theluckystrike. Chrome extension development services at zovo.one.
"""

# Define related articles for each file (file -> list of related article paths)
# These are generic mappings based on content categories
RELATED_ARTICLES = {
    # Articles can have related articles from other sections
    "articles/affiliate-model.md": ["articles/pricing-strategies.md", "articles/freemium-model.md", "articles/content-marketing.md"],
    "articles/analytics-without-tracking.md": ["articles/extension-valuation.md", "articles/scaling-solo.md", "articles/legal-essentials.md"],
    "articles/belikenative-case-study.md": ["articles/zovo-bundle-case-study.md", "articles/tab-suspender-pro-case-study.md", "articles/pricing-strategies.md"],
    "articles/case-studies-overview.md": ["articles/zovo-bundle-case-study.md", "articles/belikenative-case-study.md", "articles/tab-suspender-pro-case-study.md"],
    "articles/chrome-web-store-payments.md": ["articles/stripe-in-extensions.md", "articles/payment-integration-overview.md", "articles/pricing-strategies.md"],
    "articles/chrome-web-store-seo.md": ["articles/zero-to-1000-users.md", "articles/review-acquisition.md", "articles/content-marketing.md"],
    "articles/community-building.md": ["articles/content-marketing.md", "articles/affiliate-model.md", "articles/sponsorship-model.md"],
    "articles/content-marketing.md": ["articles/zero-to-1000-users.md", "articles/chrome-web-store-seo.md", "articles/community-building.md"],
    "articles/cross-promotion.md": ["articles/content-marketing.md", "articles/community-building.md", "articles/affiliate-model.md"],
    "articles/extension-as-a-service.md": ["articles/subscription-model.md", "articles/pricing-strategies.md", "articles/freemium-model.md"],
    "articles/extension-valuation.md": ["articles/selling-your-extension.md", "articles/scaling-solo.md", "articles/pricing-strategies.md"],
    "articles/failed-experiments.md": ["articles/pricing-strategies.md", "articles/freemium-model.md", "articles/trial-implementation.md"],
    "articles/freemium-model.md": ["articles/pricing-strategies.md", "articles/subscription-model.md", "articles/trial-implementation.md"],
    "articles/growth-playbook-overview.md": ["articles/zero-to-1000-users.md", "articles/content-marketing.md", "articles/chrome-web-store-seo.md"],
    "articles/handling-refunds.md": ["articles/legal-essentials.md", "articles/payment-integration-overview.md", "articles/pricing-strategies.md"],
    "articles/legal-essentials.md": ["articles/license-key-system.md", "articles/handling-refunds.md", "articles/server-side-validation.md"],
    "articles/license-key-system.md": ["articles/server-side-validation.md", "articles/stripe-in-extensions.md", "articles/legal-essentials.md"],
    "articles/monetization-strategies-overview.md": ["articles/pricing-strategies.md", "articles/subscription-model.md", "articles/freemium-model.md"],
    "articles/one-time-purchase.md": ["articles/pricing-strategies.md", "articles/subscription-model.md", "articles/freemium-model.md"],
    "articles/payment-integration-overview.md": ["articles/stripe-in-extensions.md", "articles/chrome-web-store-payments.md", "articles/license-key-system.md"],
    "articles/paywall-patterns.md": ["articles/trial-implementation.md", "articles/freemium-model.md", "articles/pricing-strategies.md"],
    "articles/pricing-strategies.md": ["articles/subscription-model.md", "articles/freemium-model.md", "articles/trial-implementation.md"],
    "articles/review-acquisition.md": ["articles/chrome-web-store-seo.md", "articles/zero-to-1000-users.md", "articles/content-marketing.md"],
    "articles/scaling-solo.md": ["articles/extension-valuation.md", "articles/selling-your-extension.md", "articles/legal-essentials.md"],
    "articles/selling-your-extension.md": ["articles/extension-valuation.md", "articles/pricing-strategies.md", "articles/scaling-solo.md"],
    "articles/server-side-validation.md": ["articles/license-key-system.md", "articles/stripe-in-extensions.md", "articles/trial-implementation.md"],
    "articles/sponsorship-model.md": ["articles/affiliate-model.md", "articles/community-building.md", "articles/content-marketing.md"],
    "articles/stripe-in-extensions.md": ["articles/payment-integration-overview.md", "articles/license-key-system.md", "articles/trial-implementation.md"],
    "articles/subscription-model.md": ["articles/pricing-strategies.md", "articles/freemium-model.md", "articles/one-time-purchase.md"],
    "articles/tab-suspender-pro-case-study.md": ["articles/zovo-bundle-case-study.md", "articles/belikenative-case-study.md", "articles/chrome-web-store-seo.md"],
    "articles/technical-implementation-links.md": ["articles/stripe-in-extensions.md", "articles/server-side-validation.md", "articles/license-key-system.md"],
    "articles/trial-implementation.md": ["articles/freemium-model.md", "articles/paywall-patterns.md", "articles/pricing-strategies.md"],
    "articles/update-monetization.md": ["articles/content-marketing.md", "articles/paywall-patterns.md", "articles/pricing-strategies.md"],
    "articles/zero-to-1000-users.md": ["articles/chrome-web-store-seo.md", "articles/content-marketing.md", "articles/review-acquisition.md"],
    "articles/zovo-bundle-case-study.md": ["articles/tab-sumper-pro-case-study.md", "articles/belikenative-case-study.md", "articles/pricing-strategies.md"],
    
    # docs files
    "docs/analytics/extension-analytics-complete-guide.md": ["articles/analytics-without-tracking.md", "articles/legal-essentials.md", "articles/scaling-solo.md"],
    "docs/case-studies/successful-extension-businesses.md": ["articles/zovo-bundle-case-study.md", "articles/belikenative-case-study.md", "articles/tab-suspender-pro-case-study.md"],
    "docs/getting-started/introduction.md": ["articles/monetization-strategies-overview.md", "articles/pricing-strategies.md", "articles/zero-to-1000-users.md"],
    "docs/growth/chrome-web-store-seo.md": ["articles/chrome-web-store-seo.md", "articles/zero-to-1000-users.md", "articles/review-acquisition.md"],
    "docs/growth/zero-to-1000-users.md": ["articles/zero-to-1000-users.md", "articles/chrome-web-store-seo.md", "articles/content-marketing.md"],
    "docs/payments/paypal-integration-extensions.md": ["articles/stripe-in-extensions.md", "articles/payment-integration-overview.md", "articles/chrome-web-store-payments.md"],
    "docs/payments/stripe-in-extensions.md": ["articles/stripe-in-extensions.md", "articles/payment-integration-overview.md", "articles/license-key-system.md"],
    "docs/revenue/freemium-model.md": ["articles/freemium-model.md", "articles/pricing-strategies.md", "articles/subscription-model.md"],
    "docs/revenue/in-app-purchases-extensions.md": ["articles/stripe-in-extensions.md", "articles/chrome-web-store-payments.md", "articles/payment-integration-overview.md"],
    "docs/technical-guides-index.md": ["articles/technical-implementation-links.md", "articles/server-side-validation.md", "articles/stripe-in-extensions.md"],
    
    # Root files
    "README.md": ["index.md", "articles/pricing-strategies.md", "articles/zero-to-1000-users.md"],
    "CONTRIBUTING.md": ["index.md", "articles/monetization-strategies-overview.md", "articles/content-marketing.md"],
    "resources/improved-readmes/webext-dns.md": ["articles/technical-implementation-links.md", "articles/server-side-validation.md", "articles/license-key-system.md"],
    "index.md": ["articles/pricing-strategies.md", "articles/freemium-model.md", "articles/zero-to-1000-users.md"],
}

# SEO titles and descriptions for each file (search query focused)
SEO_DATA = {
    "articles/affiliate-model.md": {
        "title": "Chrome Extension Affiliate Marketing: Monetize Through Partnerships",
        "description": "Learn how to monetize your Chrome extension through affiliate marketing. Partner with tools and earn commissions on referrals."
    },
    "articles/analytics-without-tracking.md": {
        "title": "Privacy-First Chrome Extension Analytics: Complete Guide",
        "description": "Track Chrome extension performance without invasive tracking. GDPR-compliant analytics that respect user privacy."
    },
    "articles/belikenative-case-study.md": {
        "title": "B2B Chrome Extension Monetization: Belike Native Case Study",
        "description": "How Belike Native built a successful B2B Chrome extension business. Enterprise pricing and monetization strategies."
    },
    "articles/case-studies-overview.md": {
        "title": "Chrome Extension Case Studies: Real Monetization Success Stories",
        "description": "Learn from successful Chrome extension businesses. Case studies covering pricing, growth, and revenue strategies."
    },
    "articles/chrome-web-store-payments.md": {
        "title": "Chrome Web Store Payments: Complete Setup Guide",
        "description": "Set up payment processing in the Chrome Web Store. Accept payments via Google's billing system for extensions."
    },
    "articles/chrome-web-store-seo.md": {
        "title": "Chrome Web Store SEO: Rank Higher and Get More Downloads",
        "description": "Optimize your Chrome extension for the Web Store search algorithm. Boost visibility and install rates with proven SEO tactics."
    },
    "articles/community-building.md": {
        "title": "Build a Community Around Your Chrome Extension",
        "description": "Create a loyal user community for your Chrome extension. Grow engagement and turn users into advocates."
    },
    "articles/content-marketing.md": {
        "title": "Content Marketing for Chrome Extensions: Drive Organic Growth",
        "description": "Use content marketing to grow your Chrome extension. Blog posts, guides, and SEO strategies that work."
    },
    "articles/cross-promotion.md": {
        "title": "Cross-Promote Your Chrome Extensions: strategies",
        "description": "Promote multiple Chrome extensions together. Bundle and cross-sell to maximize revenue per user."
    },
    "articles/extension-as-a-service.md": {
        "title": "Extension as a Service (EaaS): SaaS Model for Chrome Extensions",
        "description": "Treat your Chrome extension as a service. Build recurring revenue with ongoing value delivery."
    },
    "articles/extension-valuation.md": {
        "title": "How to Value Your Chrome Extension Business",
        "description": "Determine what your Chrome extension is worth. Valuation methods and metrics for extension businesses."
    },
    "articles/failed-experiments.md": {
        "title": "Chrome Extension Monetization Failures: Lessons Learned",
        "description": "Learn from failed monetization experiments. Avoid costly mistakes when monetizing your Chrome extension."
    },
    "articles/freemium-model.md": {
        "title": "Freemium Model for Chrome Extensions: Convert Free to Paid",
        "description": "Implement a freemium model for your Chrome extension. Balance free features with premium upgrades."
    },
    "articles/growth-playbook-overview.md": {
        "title": "Chrome Extension Growth Playbook: Scale Your User Base",
        "description": "Comprehensive guide to growing your Chrome extension. From zero to thousands of users with proven tactics."
    },
    "articles/handling-refunds.md": {
        "title": "Chrome Extension Refund Policy: Best Practices",
        "description": "Create a fair refund policy for your Chrome extension. Build trust while protecting your revenue."
    },
    "articles/legal-essentials.md": {
        "title": "Legal Requirements for Chrome Extensions: Terms, Privacy, Compliance",
        "description": "Navigate legal requirements for Chrome extensions. Privacy policies, terms of service, and compliance."
    },
    "articles/license-key-system.md": {
        "title": "License Key System for Chrome Extensions: Prevent Piracy",
        "description": "Implement license key validation for your Chrome extension. Server-side protection against piracy and abuse."
    },
    "articles/monetization-strategies-overview.md": {
        "title": "Chrome Extension Monetization Strategies: Complete Overview",
        "description": "Overview of all ways to monetize Chrome extensions. Compare subscription, freemium, one-time purchase, and more."
    },
    "articles/one-time-purchase.md": {
        "title": "One-Time Purchase Model for Chrome Extensions",
        "description": "Sell your Chrome extension with lifetime pricing. One-time payment vs subscription pros and cons."
    },
    "articles/payment-integration-overview.md": {
        "title": "Chrome Extension Payment Integration: Compare Providers",
        "description": "Compare payment processors for Chrome extensions. Stripe, PayPal, Paddle, and Chrome Web Store payments."
    },
    "articles/paywall-patterns.md": {
        "title": "Chrome Extension Paywall Patterns That Convert",
        "description": "Design effective paywalls for Chrome extensions. Premium gating patterns that drive upgrades."
    },
    "articles/pricing-strategies.md": {
        "title": "Chrome Extension Pricing Strategies: Data-Driven Guide",
        "description": "How to price your Chrome extension for maximum revenue. Price anchoring, tiers, and psychological pricing."
    },
    "articles/review-acquisition.md": {
        "title": "Get More Chrome Extension Reviews: Proven Strategies",
        "description": "Increase Chrome Web Store reviews for your extension. Build social proof and improve conversion rates."
    },
    "articles/scaling-solo.md": {
        "title": "Scale Your Chrome Extension Business Solo",
        "description": "Grow your Chrome extension business without employees. Systems and processes for solo developers."
    },
    "articles/selling-your-extension.md": {
        "title": "Sell Your Chrome Extension: Exit Strategies",
        "description": "Sell your Chrome extension business. Find buyers, value your business, and close the deal."
    },
    "articles/server-side-validation.md": {
        "title": "Server-Side Validation for Chrome Extensions",
        "description": "Implement secure server-side validation for Chrome extensions. Prevent tampering and license abuse."
    },
    "articles/sponsorship-model.md": {
        "title": "Sponsorship Model for Chrome Extensions",
        "description": "Monetize your Chrome extension through sponsorships. Partner with brands and earn recurring revenue."
    },
    "articles/stripe-in-extensions.md": {
        "title": "Stripe Integration for Chrome Extensions",
        "description": "Integrate Stripe payments into your Chrome extension. Subscriptions, one-time payments, and trials."
    },
    "articles/subscription-model.md": {
        "title": "Subscription Model for Chrome Extensions: Recurring Revenue",
        "description": "Implement subscription billing for Chrome extensions. Monthly and annual plans that retain users."
    },
    "articles/tab-suspender-pro-case-study.md": {
        "title": "Tab Suspender Pro Case Study: Competing in Crowded Markets",
        "description": "How Tab Suspender Pro competed and won in a crowded niche. Trust, performance, and modern standards."
    },
    "articles/technical-implementation-links.md": {
        "title": "Chrome Extension Technical Implementation Resources",
        "description": "Technical guides for building and monetizing Chrome extensions. Implementation resources and best practices."
    },
    "articles/trial-implementation.md": {
        "title": "Free Trial Implementation for Chrome Extensions",
        "description": "Implement free trials for your Chrome extension. Trial architecture, conversion optimization, and abuse prevention."
    },
    "articles/update-monetization.md": {
        "title": "Monetize Your Chrome Extension Updates",
        "description": "Use extension updates as monetization opportunities. Feature announcements and upgrade prompts that convert."
    },
    "articles/zero-to-1000-users.md": {
        "title": "Grow Your Chrome Extension from Zero to 1000 Users",
        "description": "Early stage growth tactics for Chrome extensions. Get your first 1000 users with proven strategies."
    },
    "articles/zovo-bundle-case-study.md": {
        "title": "Zovo Bundle Case Study: How 17 Extensions Generated $40K/Month",
        "description": "How bundling 17 Chrome extensions created $40K/month recurring revenue. The portfolio effect explained."
    },
    
    # docs files
    "docs/analytics/extension-analytics-complete-guide.md": {
        "title": "Complete Guide to Chrome Extension Analytics",
        "description": "Implement analytics in your Chrome extension. Track events, user behavior, and key metrics."
    },
    "docs/case-studies/successful-extension-businesses.md": {
        "title": "Successful Chrome Extension Businesses: Case Studies",
        "description": "Study successful Chrome extension businesses. Learn from developers who built profitable extensions."
    },
    "docs/getting-started/introduction.md": {
        "title": "Getting Started with Chrome Extension Monetization",
        "description": "Introduction to monetizing Chrome extensions. Choose your revenue model and start earning."
    },
    "docs/growth/chrome-web-store-seo.md": {
        "title": "Chrome Web Store SEO Guide",
        "description": "Optimize your Chrome extension listing for the Web Store. Improve visibility and get more installs."
    },
    "docs/growth/zero-to-1000-users.md": {
        "title": "Zero to 1000 Users: Chrome Extension Growth Guide",
        "description": "Grow your Chrome extension from launch to 1000 users. Early stage growth strategies that work."
    },
    "docs/payments/paypal-integration-extensions.md": {
        "title": "PayPal Integration for Chrome Extensions",
        "description": "Add PayPal payments to your Chrome extension. Offer familiar payment options to your users."
    },
    "docs/payments/stripe-in-extensions.md": {
        "title": "Stripe for Chrome Extensions: Payment Integration",
        "description": "Integrate Stripe into your Chrome extension. Accept payments with the leading payment processor."
    },
    "docs/revenue/freemium-model.md": {
        "title": "Freemium Model for Browser Extensions",
        "description": "Implement freemium for your browser extension. Balance free and paid features for maximum conversion."
    },
    "docs/revenue/in-app-purchases-extensions.md": {
        "title": "In-App Purchases for Chrome Extensions",
        "description": "Implement in-app purchases in Chrome extensions. Sell virtual goods and premium features."
    },
    "docs/technical-guides-index.md": {
        "title": "Chrome Extension Technical Guides",
        "description": "Technical guides for Chrome extension development. Implementation resources and best practices."
    },
    
    # Root files
    "README.md": {
        "title": "Extension Monetization Playbook: Monetize Chrome Extensions",
        "description": "Complete guide to monetizing Chrome extensions. Revenue models, payments, growth strategies, and case studies."
    },
    "CONTRIBUTING.md": {
        "title": "Contribute to the Extension Monetization Playbook",
        "description": "Contribute articles to the Extension Monetization Playbook. Share your Chrome extension monetization expertise."
    },
    "resources/improved-readmes/webext-dns.md": {
        "title": "Chrome DNS API TypeScript Wrapper: webext-dns",
        "description": "TypeScript wrapper for Chrome DNS API. Clean type-safe interface for DNS resolution in extensions."
    },
    "index.md": {
        "title": "Chrome Extension Monetization Playbook: Complete Guide",
        "description": "The definitive guide to monetizing Chrome extensions. Proven strategies from real-world case studies."
    },
}


def has_front_matter(content):
    """Check if content has Jekyll front matter."""
    return content.startswith('---')


def extract_front_matter(content):
    """Extract existing front matter if present."""
    if not has_front_matter(content):
        return None, content
    
    parts = content.split('---', 2)
    if len(parts) >= 3:
        return parts[1], parts[2]
    return None, content


def generate_related_section(related_files):
    """Generate the Related Articles section."""
    if not related_files:
        return ""
    
    section = "\n\n## Related Articles\n\n"
    for f in related_files:
        # Convert file path to display name
        filename = os.path.basename(f)
        name = filename.replace('.md', '').replace('-', ' ').title()
        section += f"- [{name}]({f})\n"
    
    return section


def process_file(filepath):
    """Process a single markdown file."""
    print(f"Processing: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Get relative path for lookups
    rel_path = os.path.relpath(filepath, '.')
    
    # Get SEO data
    seo = SEO_DATA.get(rel_path, {
        "title": "Chrome Extension Monetization",
        "description": "Learn how to monetize your Chrome extension effectively."
    })
    
    # Check if has existing front matter
    if has_front_matter(content):
        # Extract existing front matter and body
        front_matter, body = extract_front_matter(content)
        
        # Parse existing front matter
        lines = front_matter.strip().split('\n')
        new_front_matter = []
        has_layout = False
        has_title = False
        has_description = False
        
        for line in lines:
            if line.startswith('layout:'):
                new_front_matter.append('layout: default')
                has_layout = True
            elif line.startswith('title:'):
                new_front_matter.append(f'title: "{seo["title"]}"')
                has_title = True
            elif line.startswith('description:'):
                new_front_matter.append(f'description: "{seo["description"]}"')
                has_description = True
            else:
                new_front_matter.append(line)
        
        if not has_layout:
            new_front_matter.insert(0, 'layout: default')
        if not has_title:
            new_front_matter.insert(1, f'title: "{seo["title"]}"')
        if not has_description:
            new_front_matter.insert(2, f'description: "{seo["description"]}"')
        
        # Rebuild front matter
        new_front_matter_str = '---\n' + '\n'.join(new_front_matter) + '\n---'
        
        # Check if footer already exists
        if "Part of the Extension Monetization Playbook" not in body:
            body = body.rstrip() + FOOTER
        
        # Check if related articles section exists
        if "## Related Articles" not in body and rel_path in RELATED_ARTICLES:
            related = generate_related_section(RELATED_ARTICLES[rel_path])
            body = body.rstrip() + related
        
        new_content = new_front_matter_str + body
    
    else:
        # Add new front matter
        front_matter = f"""---
layout: default
title: "{seo["title"]}"
description: "{seo["description"]}"
---

"""
        
        # Check if footer already exists
        if "Part of the Extension Monetization Playbook" not in content:
            content = content.rstrip() + FOOTER
        
        # Check if related articles section exists
        if "## Related Articles" not in content and rel_path in RELATED_ARTICLES:
            related = generate_related_section(RELATED_ARTICLES[rel_path])
            content = content.rstrip() + related
        
        new_content = front_matter + content
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"  Updated: {rel_path}")


def main():
    """Main function to process all markdown files."""
    # Find all markdown files
    md_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.md'):
                md_files.append(os.path.join(root, file))
    
    print(f"Found {len(md_files)} markdown files")
    
    # Process each file
    for filepath in md_files:
        try:
            process_file(filepath)
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
