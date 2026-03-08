#!/usr/bin/env python3
"""
Script to fix README and other root files with better SEO descriptions.
"""
import os
import re
from pathlib import Path

BASE_DIR = Path("/Users/mike/zovo-workspaces/a7/extension-monetization-playbook")

# Specific SEO content for root files
ROOT_FILES_SEO = {
    "README.md": {
        "title": "Extension Monetization Playbook",
        "description": "Complete guide to monetizing Chrome extensions. Proven strategies, revenue models, and case studies from successful extension developers."
    },
    "index.md": {
        "title": "Chrome Extension Monetization Playbook",
        "description": "The definitive guide to making money from Chrome extensions. 30+ articles covering freemium, subscriptions, payments, and growth."
    },
    "CONTRIBUTING.md": {
        "title": "Contributing to Extension Monetization Playbook",
        "description": "How to contribute to the Extension Monetization Playbook. Guidelines for submitting articles and improving the guide."
    }
}

def process_root_files():
    for filename, seo in ROOT_FILES_SEO.items():
        filepath = BASE_DIR / filename
        if filepath.exists():
            print(f"Fixing: {filename}")
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check if already has front matter
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    # Replace description in existing front matter
                    existing_fm = parts[1]
                    body = parts[2]
                    
                    # Rebuild front matter with new values
                    front_matter = f"""---
layout: default
title: "{seo['title']}"
description: "{seo['description']}"
---
"""
                    content = front_matter + body
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  Fixed: {seo['title']}")

if __name__ == "__main__":
    process_root_files()
    print("Done!")
