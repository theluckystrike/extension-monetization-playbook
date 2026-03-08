#!/usr/bin/env python3
"""
Script to add Jekyll front matter, footer, and related articles to all markdown files.
Fixed version to handle duplicates properly.
"""
import os
import re
from pathlib import Path

# Base directory
BASE_DIR = Path("/Users/mike/zovo-workspaces/a7/extension-monetization-playbook")

# Footer to add to each article
FOOTER = """

---

Part of the Extension Monetization Playbook by theluckystrike. Chrome extension development services at zovo.one.
"""

# Related articles to link (common articles in the playbook)
RELATED_ARTICLES = """## Related Articles

- [Freemium Model](/articles/freemium-model) - Balance free and paid features to maximize conversion
- [Subscription Model](/articles/subscription-model) - Recurring revenue strategies for extensions
- [Stripe Integration](/articles/stripe-in-extensions) - Complete payment processing guide
"""

# SEO-optimized titles and descriptions for different article topics
SEO_TITLES = {
    "trial-implementation": ("Free Trial Implementation for Chrome Extensions", 
        "Learn how to implement effective free trials for Chrome extensions. Boost conversion rates with proven trial strategies."),
    "subscription-model": ("Chrome Extension Subscription Pricing Guide",
        "Master subscription pricing for Chrome extensions. Learn recurring revenue strategies, churn reduction, and Stripe integration."),
    "freemium-model": ("Chrome Extension Freemium Model Guide",
        "Build a successful freemium model for your Chrome extension. Feature gating, conversion optimization, and usage limits."),
    "pricing-strategies": ("Chrome Extension Pricing Strategies",
        "Optimize your Chrome extension pricing for maximum revenue. Pricing models, psychological anchoring, and tier strategies."),
    "one-time-purchase": ("Chrome Extension One-Time Purchase Model",
        "Implement one-time purchase pricing for browser extensions. Lifetime deals, license keys, and sustainable revenue."),
    "sponsorship-model": ("Chrome Extension Sponsorship Monetization",
        "Monetize your Chrome extension through sponsorships. Brand deals, ad integration, and partnership strategies."),
    "community-building": ("Chrome Extension Community Building",
        "Build an engaged community around your Chrome extension. User groups, feedback loops, and advocacy programs."),
    "selling-your-extension": ("Selling Your Chrome Extension",
        "Complete guide to selling your Chrome extension. Valuation, due diligence, and exit strategies for extension businesses."),
    "extension-as-a-service": ("Extension as a Service Business Model",
        "Build a scalable Extension as a Service business. Recurring revenue, SaaS principles, and growth strategies."),
    "license-key-system": ("Chrome Extension License Key System",
        "Implement a secure license key system for Chrome extensions. Anti-piracy, validation, and key management."),
    "stripe-in-extensions": ("Stripe Integration for Chrome Extensions",
        "Complete guide to integrating Stripe payments in Chrome extensions. Checkout, subscriptions, and webhooks."),
    "legal-essentials": ("Chrome Extension Legal Essentials",
        "Legal requirements for Chrome extensions. Privacy policies, terms of service, and compliance guide."),
    "case-studies-overview": ("Chrome Extension Monetization Case Studies",
        "Learn from successful Chrome extension monetization case studies. Real strategies from profitable extensions."),
    "paywall-patterns": ("Chrome Extension Paywall Patterns",
        "Design effective paywalls for Chrome extensions. Conversion-optimized patterns and best practices."),
    "technical-implementation-links": ("Chrome Extension Technical Implementation",
        "Technical resources for Chrome extension development. Links to guides, tools, and documentation."),
    "payment-integration-overview": ("Chrome Extension Payment Integration Guide",
        "Overview of payment integration options for Chrome extensions. Stripe, PayPal, Paddle, and more."),
    "failed-experiments": ("Chrome Extension Monetization Failures",
        "Learn from failed Chrome extension monetization experiments. What not to do and common mistakes to avoid."),
    "analytics-without-tracking": ("Privacy-First Analytics for Chrome Extensions",
        "Implement analytics in Chrome extensions without tracking users. Privacy-compliant analytics solutions."),
    "extension-valuation": ("Chrome Extension Valuation Guide",
        "Learn how to value your Chrome extension business. Metrics, multiples, and valuation methods."),
    "handling-refunds": ("Chrome Extension Refund Handling",
        "Best practices for handling refunds in Chrome extensions. Policies, automation, and customer service."),
    "update-monetization": ("Updating Monetized Chrome Extensions",
        "Strategies for updating monetized Chrome extensions. Evolve without alienating paying users."),
    "review-acquisition": ("Chrome Extension Review Acquisition",
        "Get more reviews for your Chrome extension. Review strategies, follow-ups, and rating optimization."),
    "chrome-web-store-seo": ("Chrome Web Store SEO Guide",
        "Optimize your Chrome Web Store listing for search. Keywords, descriptions, and visibility strategies."),
    "chrome-web-store-payments": ("Chrome Web Store Payments Setup",
        "Set up payments in the Chrome Web Store. Google Play Billing, payouts, and payment configuration."),
    "server-side-validation": ("Chrome Extension Server-Side Validation",
        "Implement server-side validation for Chrome extensions. License verification, security, and best practices."),
    "monetization-strategies-overview": ("Chrome Extension Monetization Strategies",
        "Comprehensive guide to Chrome extension monetization. Revenue models, pricing, and growth strategies."),
    "zero-to-1000-users": ("Grow Your Chrome Extension to 1000 Users",
        "Proven strategies to grow your Chrome extension from zero to 1000 users. Organic growth and user acquisition."),
    "scaling-solo": ("Scaling Your Chrome Extension Solo",
        "Scale your Chrome extension business as a solo developer. Time management, automation, and growth."),
    "content-marketing": ("Content Marketing for Chrome Extensions",
        "Drive traffic to your Chrome extension with content marketing. SEO, blogging, and content strategies."),
    "tab-suspender-pro-case-study": ("Tab Suspender Pro Case Study",
        "Case study: How Tab Suspender Pro built a successful Chrome extension business. Lessons and strategies."),
    "cross-promotion": ("Chrome Extension Cross-Promotion",
        "Cross-promote your Chrome extensions. Bundle deals, cross-listing, and user migration strategies."),
    "zovo-bundle-case-study": ("Zovo Bundle Case Study",
        "Case study: The Zovo extension bundle strategy. How multiple extensions drive revenue together."),
    "belikenative-case-study": ("Belike Native Case Study",
        "Case study: Building a successful native extension business. Strategies and lessons learned."),
    "affiliate-model": ("Chrome Extension Affiliate Marketing",
        "Monetize your Chrome extension with affiliate marketing. Commission strategies and implementation."),
    "growth-playbook-overview": ("Chrome Extension Growth Playbook",
        "Comprehensive growth strategies for Chrome extensions. User acquisition, retention, and scaling."),
}

def get_default_seo_content(filename, content):
    """Generate SEO content for files without specific mapping."""
    name = os.path.basename(filename).replace('.md', '').replace('-', ' ').title()
    first_line = content.split('\n')[0] if content else ""
    
    if first_line.startswith('#'):
        title = first_line.replace('#', '').strip()
        if 'Chrome' not in title and 'extension' not in title.lower():
            title = f"Chrome Extension {title}"
    else:
        title = f"Chrome Extension {name}"
    
    sentences = re.split(r'[.!?]', content)
    description = ""
    for s in sentences[:3]:
        s = s.strip()
        if len(s) > 20:
            description += s + ". "
        if len(description) > 140:
            break
    description = description.strip()[:155]
    
    if not description:
        description = f"Learn how to monetize your Chrome extension with proven strategies and best practices."
    
    return title, description

def clean_body(body):
    """Clean the body content by removing existing related articles and footers."""
    # Remove existing Related Articles sections (case insensitive header)
    body = re.sub(r'\n## Related Articles\n.*?(?=\n---|\n## |\Z)', '', body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r'\n## *Related.*?\n.*?(?=\n---|\n## |\Z)', '', body, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove existing footers (Part of the Extension Monetization Playbook)
    footer_pattern = r"\n*---\n*Part of the Extension Monetization Playbook.*?zovo\.one\.*"
    body = re.sub(footer_pattern, '', body, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove "Built by Zovo" lines at the end
    body = re.sub(r'\n*---\n*Built by \[Zovo\].*', '', body, flags=re.DOTALL)
    
    return body.strip()

def process_file(filepath):
    """Process a single markdown file."""
    print(f"Processing: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    body = content
    existing_title = ""
    existing_description = ""
    
    # Check if file already has front matter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            existing_front_matter = parts[1]
            body = parts[2]
            
            # Extract existing title and description
            for line in existing_front_matter.split('\n'):
                if line.startswith('title:'):
                    existing_title = line.split(':', 1)[1].strip().strip('"')
                elif line.startswith('description:'):
                    existing_description = line.split(':', 1)[1].strip().strip('"')
    
    # Get filename for SEO lookup
    filename = os.path.basename(filepath)
    basename = filename.replace('.md', '')
    
    # Check if we have specific SEO content for this file
    if basename in SEO_TITLES:
        title, description = SEO_TITLES[basename]
    else:
        title, description = get_default_seo_content(filename, body)
    
    # Use existing title/description if they exist and are reasonable
    if existing_title and len(existing_title) > 5:
        title = existing_title
    if existing_description and len(existing_description) > 20:
        if len(existing_description) < 160:
            description = existing_description
    
    # Ensure description is under 160 chars
    if len(description) > 159:
        description = description[:156].rsplit(' ', 1)[0] + '...'
    
    # Build front matter
    front_matter = f"""---
layout: default
title: "{title}"
description: "{description}"
---
"""
    
    # Clean the body
    body = clean_body(body)
    
    # Add Related Articles and Footer
    new_content = body + "\n" + RELATED_ARTICLES + FOOTER
    
    # Combine with front matter
    final_content = front_matter + new_content
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)
    
    print(f"  Updated: {title[:50]}...")

def main():
    """Process all markdown files."""
    md_files = []
    
    # Find all .md files
    for root, dirs, files in os.walk(BASE_DIR):
        for file in files:
            if file.endswith('.md'):
                filepath = os.path.join(root, file)
                md_files.append(filepath)
    
    print(f"Found {len(md_files)} markdown files")
    
    for filepath in md_files:
        try:
            process_file(filepath)
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    
    print("Done!")

if __name__ == "__main__":
    main()
