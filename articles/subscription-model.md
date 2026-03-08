---
layout: default
title: "Subscription Model for Chrome Extensions: Architecture & Implementation"
description: "Build a subscription-based Chrome extension business. Learn license validation, churn prevention, tier management, and subscription lifecycle handling with TypeScript."
permalink: /revenue/subscription-model/
---

# Subscription Model for Chrome Extensions: Architecture & Implementation

Subscriptions represent the gold standard for browser extension revenue when implemented correctly. Unlike one-time purchases, subscriptions provide predictable Monthly Recurring Revenue (MRR), significantly higher Lifetime Value (LTV), and a sustainable business model that funds ongoing development. However, the technical architecture required to support subscriptions in extensions presents unique challenges that differ substantially from traditional SaaS applications.

This comprehensive guide covers the complete subscription implementation stack: from system architecture and license validation to churn prevention and metrics tracking. Each section includes production-ready TypeScript code that you can adapt for your extension.

## Why Subscriptions Excel for Extensions

The fundamental economics of subscriptions favor extensions that deliver continuous value. A one-time purchase of $49 generates revenue exactly once, while a $5/month subscription that retains users for 24 months generates $120 from the same customer—roughly 2.5x the LTV. For extensions with ongoing costs like server infrastructure, AI API calls, or content updates, subscriptions align costs with revenue in a way that one-time purchases cannot.

Subscriptions make sense when your extension provides value on an ongoing basis. Server-side processing, cross-device synchronization, continuously updated data feeds, and AI-powered features all justify recurring charges because they incur ongoing costs. If your extension operates entirely offline with no backend dependencies, subscriptions face an uphill battle—users will question why they're paying monthly for software that never connects to servers.

The key differentiator is perceived value versus perceived cost. Users resist $5/month for something they open occasionally, but readily pay for extensions that save them hours weekly or generate measurable income. Frame your subscription around outcomes: "Save 10 hours every week" resonates more than "Advanced filtering included."

For more on when subscriptions versus one-time payments make sense, see our [Freemium Model](articles/freemium-model.md) guide.

## Subscription Architecture for Extensions

A robust subscription system requires multiple components working together: the extension itself, your backend API, and your payment processor (typically Stripe). Understanding how these pieces communicate is essential for building a reliable system.

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        SUBSCRIPTION SYSTEM ARCHITECTURE                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐         ┌──────────────┐         ┌──────────────────┐     │
│  │   BROWSER    │         │   BACKEND    │         │    STRIPE        │     │
│  │  EXTENSION   │◄───────►│     API      │◄───────►│  PAYMENT GATEWAY │     │
│  └──────────────┘         └──────────────┘         └──────────────────┘     │
│         │                       │                        │                   │
│         │                       │                        │                   │
│  ┌──────▼──────┐         ┌──────▼──────┐          ┌─────▼─────┐            │
│  │   CHROME    │         │  DATABASE   │          │  WEBHOOKS │            │
│  │   STORAGE   │         │  (LICENSE)  │          │  EVENTS   │            │
│  └─────────────┘         └─────────────┘          └───────────┘            │
│         │                       │                                           │
│         │                       │                                           │
│  ┌──────▼───────────────────────▼─────────────────────────────────┐        │
│  │                    LICENSE VALIDATION FLOW                       │        │
│  │                                                                   │        │
│  │  1. Extension starts ──► Check chrome.storage.cache             │        │
│  │         │                         │                             │        │
│  │         ▼                         ▼                             │        │
│  │  2. Cache valid? ──YES──► Grant premium access                 │        │
│  │         │NO                                                    │        │
│  │         ▼                                                      │        │
│  │  3. Online? ──YES──► Call Backend /api/validate                │        │
│  │         │NO              │              │                      │        │
│  │         ▼               ▼              ▼                       │        │
│  │  4. Grace period? ──YES──► Grant access + show warning        │        │
│  │         │NO                                                    │        │
│  │         ▼                                                      │        │
│  │  5. Show paywall, require subscription                         │        │
│  │                                                                   │        │
│  └───────────────────────────────────────────────────────────────────┘        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow Description

The subscription lifecycle flows through several stages:

1. **Initial Purchase**: User completes Stripe Checkout, webhook fires to your backend, license created in database
2. **Extension Startup**: Extension loads, checks cached license status, validates with backend if online
3. **Feature Access**: Each premium feature checks license status before execution
4. **Periodic Validation**: Background alarm triggers re-validation every N hours
5. **Payment Events**: Stripe webhooks update license status (renewal, failure, cancellation)

For Stripe integration details, see [Stripe in Extensions](articles/stripe-in-extensions.md).

### Cross-Device License Sync

Chrome's `chrome.storage.sync` API enables automatic synchronization of license data across devices:

```typescript
interface LicenseState {
  licenseKey: string;
  tier: SubscriptionTier;
  validUntil: number; // Unix timestamp
  lastValidated: number;
  gracePeriodUntil?: number;
}

class LicenseStorage {
  private static readonly STORAGE_KEY = 'subscription_license';

  static async saveLicense(license: LicenseState): Promise<void> {
    await chrome.storage.sync.set({
      [this.STORAGE_KEY]: license,
    });
  }

  static async getLicense(): Promise<LicenseState | null> {
    const result = await chrome.storage.sync.get(this.STORAGE_KEY);
    return result[this.STORAGE_KEY] || null;
  }

  static async clearLicense(): Promise<void> {
    await chrome.storage.sync.remove(this.STORAGE_KEY);
  }
}
```

## License Validation System

The license validator is the core security component that enforces your subscription model. It must handle startup validation, periodic re-validation, offline grace periods, and cache management.

### Complete LicenseValidator Implementation

```typescript
import { LicenseStorage, LicenseState } from './license-storage';

enum SubscriptionTier {
  FREE = 'free',
  BASIC = 'basic',
  PRO = 'pro',
  ENTERPRISE = 'enterprise',
}

interface ValidationResult {
  isValid: boolean;
  tier: SubscriptionTier;
  expiresAt: number;
  gracePeriodUntil?: number;
  error?: string;
}

class LicenseValidator {
  private readonly apiBaseUrl: string;
  private readonly gracePeriodDays: number = 7;
  private readonly validationIntervalHours: number = 6;
  private readonly offlineThresholdHours: number = 24;

  constructor(apiBaseUrl: string) {
    this.apiBaseUrl = apiBaseUrl;
  }

  /**
   * Validate license on extension startup
   * Checks cache first, then validates with server if online
   */
  async validateOnStartup(): Promise<ValidationResult> {
    // Step 1: Check cached license
    const cached = await LicenseStorage.getLicense();
    
    if (!cached) {
      return this.invalidResult('No license found');
    }

    // Step 2: Check if we're online
    if (!navigator.onLine) {
      return this.handleOffline(cached);
    }

    // Step 3: Validate with server
    try {
      const serverResult = await this.validateWithServer(cached.licenseKey);
      
      if (serverResult.isValid) {
        // Cache the fresh result
        await this.cacheResult(serverResult);
        return serverResult;
      } else {
        // License invalid on server - check grace period
        return this.handleInvalidLicense(cached, serverResult);
      }
    } catch (error) {
      // Network error - fall back to cached validation
      console.warn('Server validation failed, using cached:', error);
      return this.validateCachedResult(cached);
    }
  }

  /**
   * Set up periodic background validation using chrome.alarms
   */
  async validatePeriodically(): Promise<void> {
    // Check if alarm already exists
    const alarm = await chrome.alarms.get('license-validation');
    
    if (!alarm) {
      // Create new periodic alarm
      chrome.alarms.create('license-validation', {
        delayInMinutes: this.validationIntervalHours * 60,
        periodInMinutes: this.validationIntervalHours * 60,
      });
    }

    // Listen for alarm events
    chrome.alarms.onAlarm.addListener((alarm) => {
      if (alarm.name === 'license-validation') {
        this.validateOnStartup().catch(console.error);
      }
    });
  }

  /**
   * Handle offline scenarios with grace period logic
   */
  private handleOffline(cached: LicenseState): ValidationResult {
    const now = Date.now();
    const hoursSinceLastValidation = 
      (now - cached.lastValidated) / (1000 * 60 * 60);

    // Within offline threshold - allow access
    if (hoursSinceLastValidation < this.offlineThresholdHours) {
      return {
        isValid: true,
        tier: cached.tier as SubscriptionTier,
        expiresAt: cached.validUntil,
        gracePeriodUntil: cached.gracePeriodUntil,
      };
    }

    // Outside threshold - check if in grace period
    if (cached.gracePeriodUntil && now < cached.gracePeriodUntil) {
      return {
        isValid: true,
        tier: cached.tier as SubscriptionTier,
        expiresAt: cached.validUntil,
        gracePeriodUntil: cached.gracePeriodUntil,
      };
    }

    // Offline too long and no valid grace period
    return this.invalidResult('Offline too long, please reconnect');
  }

  /**
   * Handle license that's invalid on server but may have grace period
   */
  private handleInvalidLicense(
    cached: LicenseState, 
    serverResult: ValidationResult
  ): ValidationResult {
    const now = Date.now();
    
    // If we have an active grace period, allow access
    if (cached.gracePeriodUntil && now < cached.gracePeriodUntil) {
      return {
        isValid: true,
        tier: cached.tier as SubscriptionTier,
        expiresAt: cached.validUntil,
        gracePeriodUntil: cached.gracePeriodUntil,
      };
    }

    // No grace period - license is truly invalid
    return {
      isValid: false,
      tier: SubscriptionTier.FREE,
      expiresAt: 0,
      error: serverResult.error || 'License expired or revoked',
    };
  }

  /**
   * Validate cached result considering expiration and grace periods
   */
  private validateCachedResult(cached: LicenseState): ValidationResult {
    const now = Date.now();
    
    // Check if explicitly expired
    if (cached.validUntil && now > cached.validUntil) {
      // Check grace period
      if (cached.gracePeriodUntil && now < cached.gracePeriodUntil) {
        return {
          isValid: true,
          tier: cached.tier as SubscriptionTier,
          expiresAt: cached.validUntil,
          gracePeriodUntil: cached.gracePeriodUntil,
        };
      }
      
      return this.invalidResult('License expired');
    }

    // Cache is still valid
    return {
      isValid: true,
      tier: cached.tier as SubscriptionTier,
      expiresAt: cached.validUntil,
      gracePeriodUntil: cached.gracePeriodUntil,
    };
  }

  /**
   * Cache validation result with timestamp
   */
  private async cacheResult(result: ValidationResult): Promise<void> {
    const licenseState: LicenseState = {
      licenseKey: '', // Would be stored separately or from original cache
      tier: result.tier,
      validUntil: result.expiresAt,
      lastValidated: Date.now(),
      gracePeriodUntil: result.gracePeriodUntil,
    };
    
    await LicenseStorage.saveLicense(licenseState);
  }

  private async validateWithServer(licenseKey: string): Promise<ValidationResult> {
    const response = await fetch(`${this.apiBaseUrl}/api/license/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ licenseKey }),
    });

    if (!response.ok) {
      throw new Error(`Validation request failed: ${response.status}`);
    }

    return response.json();
  }

  private invalidResult(error: string): ValidationResult {
    return {
      isValid: false,
      tier: SubscriptionTier.FREE,
      expiresAt: 0,
      error,
    };
  }
}
```

This validator handles the critical edge cases: offline usage, grace periods after payment failures, and cache expiration. Production implementations should add rate limiting, more sophisticated error handling, and detailed logging.

## Subscription Tiers

Structuring subscription tiers requires balancing simplicity with value differentiation. Most successful extensions offer three to four tiers, with clear feature differentiation at each level.

### Tier Structure Example

| Feature | Free | Basic ($2.99/mo) | Pro ($4.99/mo) | Enterprise ($19.99/mo) |
|---------|------|------------------|----------------|------------------------|
| Core Features | ✓ | ✓ | ✓ | ✓ |
| Daily API Calls | 10 | 100 | Unlimited | Unlimited |
| Export Options | CSV | CSV, JSON | All formats | All + Custom |
| Priority Support | - | - | Email | Dedicated |
| Team Features | - | - | - | 5+ seats |
| Custom Integrations | - | - | - | ✓ |

### Feature Flags Implementation

```typescript
// Define subscription tiers as a type-safe enum
enum SubscriptionTier {
  FREE = 'free',
  BASIC = 'basic',
  PRO = 'pro',
  ENTERPRISE = 'enterprise',
}

// Define all possible features as a const type
type FeatureName = 
  | 'advanced_filters'
  | 'unlimited_api_calls'
  | 'csv_export'
  | 'json_export'
  | 'custom_export'
  | 'priority_support'
  | 'team_management'
  | 'custom_integrations'
  | 'api_access'
  | 'webhook_triggers';

// Feature flags configuration
interface FeatureFlags {
  advanced_filters: boolean;
  unlimited_api_calls: boolean;
  csv_export: boolean;
  json_export: boolean;
  custom_export: boolean;
  priority_support: boolean;
  team_management: boolean;
  custom_integrations: boolean;
  api_access: boolean;
  webhook_triggers: boolean;
}

// Tier configuration maps each tier to its feature set
const TIER_CONFIG: Record<SubscriptionTier, FeatureFlags> = {
  [SubscriptionTier.FREE]: {
    advanced_filters: false,
    unlimited_api_calls: false,
    csv_export: true,
    json_export: false,
    custom_export: false,
    priority_support: false,
    team_management: false,
    custom_integrations: false,
    api_access: false,
    webhook_triggers: false,
  },
  [SubscriptionTier.BASIC]: {
    advanced_filters: true,
    unlimited_api_calls: false,
    csv_export: true,
    json_export: true,
    custom_export: false,
    priority_support: false,
    team_management: false,
    custom_integrations: false,
    api_access: false,
    webhook_triggers: false,
  },
  [SubscriptionTier.PRO]: {
    advanced_filters: true,
    unlimited_api_calls: true,
    csv_export: true,
    json_export: true,
    custom_export: true,
    priority_support: true,
    team_management: false,
    custom_integrations: false,
    api_access: true,
    webhook_triggers: true,
  },
  [SubscriptionTier.ENTERPRISE]: {
    advanced_filters: true,
    unlimited_api_calls: true,
    csv_export: true,
    json_export: true,
    custom_export: true,
    priority_support: true,
    team_management: true,
    custom_integrations: true,
    api_access: true,
    webhook_triggers: true,
  },
};

// Service class for checking features
class FeatureManager {
  private currentTier: SubscriptionTier;
  private customFeatures: Set<string> = new Set();

  constructor(tier: SubscriptionTier) {
    this.currentTier = tier;
  }

  /**
   * Check if a specific feature is available
   */
  hasFeature(feature: FeatureName): boolean {
    // Check custom feature overrides first
    if (this.customFeatures.has(feature)) {
      return true;
    }
    
    return TIER_CONFIG[this.currentTier][feature];
  }

  /**
   * Get all feature flags for the current tier
   */
  getAllFeatures(): FeatureFlags {
    return { ...TIER_CONFIG[this.currentTier] };
  }

  /**
   * Upgrade tier - immediately updates features
   */
  upgradeTier(newTier: SubscriptionTier): void {
    this.currentTier = newTier;
    this.notifyFeatureChange();
  }

  /**
   * Downgrade tier - features remain until period end
   * (Caller should handle delayed effect)
   */
  scheduleDowngrade(newTier: SubscriptionTier, effectiveDate: number): void {
    // Store scheduled downgrade - actual change happens when date passes
    setTimeout(() => {
      if (Date.now() >= effectiveDate) {
        this.currentTier = newTier;
        this.notifyFeatureChange();
      }
    }, effectiveDate - Date.now());
  }

  private notifyFeatureChange(): void {
    // Notify UI of feature changes
    chrome.runtime.sendMessage({
      type: 'FEATURES_UPDATED',
      features: this.getAllFeatures(),
    }).catch(console.error);
  }
}
```

This implementation supports immediate upgrades and scheduled downgrades (which take effect at the end of the billing period).

## Churn Prevention Strategies

Churn is the silent killer of subscription businesses. A 5% monthly churn rate means you'd lose half your customers within a year. For extensions, where uninstallation is trivially easy, preventing churn requires both technical systems and product strategies.

### ChurnPrevention Service

```typescript
interface UsageMetrics {
  featureUsesThisMonth: number;
  hoursSavedThisMonth: number;
  lastActiveDate: number;
  totalSessions: number;
}

interface ChurnPreventionConfig {
  warningThresholdDays: number;
  criticalThresholdDays: number;
  minUsageForEngaged: number;
}

class ChurnPrevention {
  private config: ChurnPreventionConfig = {
    warningThresholdDays: 14,
    criticalThresholdDays: 30,
    minUsageForEngaged: 10,
  };

  /**
   * Check user engagement and trigger appropriate interventions
   */
  async assessEngagement(userId: string): Promise<ChurnRiskLevel> {
    const metrics = await this.getUsageMetrics(userId);
    const daysSinceActive = this.daysSince(metrics.lastActiveDate);
    
    if (daysSinceActive >= this.config.criticalThresholdDays) {
      return ChurnRiskLevel.CRITICAL;
    }
    
    if (daysSinceActive >= this.config.warningThresholdDays) {
      return ChurnRiskLevel.WARNING;
    }
    
    if (metrics.featureUsesThisMonth < this.config.minUsageForEngaged) {
      return ChurnRiskLevel.LOW_ENGAGEMENT;
    }
    
    return ChurnRiskLevel.HEALTHY;
  }

  /**
   * Generate personalized value summary for users
   */
  async generateValueSummary(userId: string): Promise<string> {
    const metrics = await this.getUsageMetrics(userId);
    
    const hoursSaved = this.estimateHoursSaved(metrics);
    const moneySaved = hoursSaved * 20; // Assume $20/hour value
    
    return `You saved ${hoursSaved} hours this month (worth ~$${moneySaved}) ` +
           `with ${metrics.featureUsesThisMonth} feature uses.`;
  }

  /**
   * Handle payment failure with grace period and notifications
   */
  async handlePaymentFailure(
    userId: string, 
    subscriptionEndDate: number
  ): Promise<void> {
    const gracePeriodEnd = Date.now() + (7 * 24 * 60 * 60 * 1000); // 7 days
    
    // Store grace period in license state
    await this.updateGracePeriod(userId, gracePeriodEnd);
    
    // Show in-extension notice
    await this.showPaymentFailureNotice(userId, gracePeriodEnd);
    
    // Send email notifications
    await this.sendPaymentFailureEmails(userId, gracePeriodEnd);
  }

  /**
   * Show payment failure notice in extension
   */
  private async showPaymentFailureNotice(
    userId: string, 
    gracePeriodEnd: number
  ): Promise<void> {
    const daysRemaining = Math.ceil(
      (gracePeriodEnd - Date.now()) / (1000 * 60 * 60 * 24)
    );
    
    // Store notice to show on next extension open
    await chrome.storage.local.set({
      paymentFailureNotice: {
        show: true,
        daysRemaining,
        actionUrl: 'https://yourapp.com/update-payment',
      },
    });
    
    // Create notification
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/warning.png',
      title: 'Payment Failed',
      message: `Update your payment method within ${daysRemaining} days to maintain access.`,
      priority: 2,
    });
  }

  /**
   * Cancellation flow with save offers
   */
  async handleCancellationAttempt(
    userId: string,
    reason: string
  ): Promise<CancellationOffer | null> {
    const usage = await this.getUsageMetrics(userId);
    
    // High-value users get retention offers
    if (usage.featureUsesThisMonth > 50) {
      return {
        type: 'discount',
        discount: '30%',
        duration: 3,
        message: 'We\'d hate to lose you! Here\'s 30% off for 3 months.',
      };
    }
    
    // Medium engagement users get survey + pause option
    if (usage.featureUsesThisMonth > 10) {
      return {
        type: 'pause',
        duration: 3,
        message: 'Consider pausing instead of canceling. ' +
                 'You\'ll keep access but won\'t be billed for 3 months.',
      };
    }
    
    // Log low-engagement cancellations for product improvement
    await this.logCancellationReason(userId, reason);
    
    return null;
  }

  private async getUsageMetrics(userId: string): Promise<UsageMetrics> {
    // Retrieve from your analytics/metrics backend
    const response = await fetch(`/api/users/${userId}/usage`);
    return response.json();
  }

  private daysSince(timestamp: number): number {
    return Math.floor((Date.now() - timestamp) / (1000 * 60 * 60 * 24));
  }

  private estimateHoursSaved(metrics: UsageMetrics): number {
    // Estimate based on feature uses
    return Math.round(metrics.featureUsesThisMonth * 0.25); // ~15 min per use
  }

  private async updateGracePeriod(
    userId: string, 
    gracePeriodEnd: number
  ): Promise<void> {
    // Update in your database
    await fetch(`/api/users/${userId}/grace-period`, {
      method: 'POST',
      body: JSON.stringify({ gracePeriodEnd }),
    });
  }

  private async sendPaymentFailureEmails(
    userId: string, 
    gracePeriodEnd: number
  ): Promise<void> {
    // Trigger email sequence from your backend
    await fetch(`/api/email/payment-failure`, {
      method: 'POST',
      body: JSON.stringify({ userId, gracePeriodEnd }),
    });
  }

  private async logCancellationReason(
    userId: string, 
    reason: string
  ): Promise<void> {
    await fetch('/api/analytics/cancellation', {
      method: 'POST',
      body: JSON.stringify({ userId, reason, timestamp: Date.now() }),
    });
  }
}

enum ChurnRiskLevel {
  HEALTHY = 'healthy',
  WARNING = 'warning',
  CRITICAL = 'critical',
  LOW_ENGAGEMENT = 'low_engagement',
}

interface CancellationOffer {
  type: 'discount' | 'pause' | 'upgrade';
  discount?: string;
  duration?: number;
  message: string;
}
```

This service implements the three pillars of churn prevention: usage tracking that demonstrates value, graceful payment failure handling, and intelligent cancellation flows that attempt to retain users before they leave.

## Trial Period Implementation

Trials convert interested users into paying customers by reducing commitment friction. Effective trials balance generosity (enough time to experience value) with scarcity (urgency to convert).

### TrialManager Implementation

```typescript
interface TrialConfig {
  durationDays: number;
  features: string[];
  usageLimit?: number;
  conversionGoal: string;
}

interface TrialState {
  trialId: string;
  startDate: number;
  endDate: number;
  featuresUnlocked: string[];
  usesRemaining?: number;
  converted: boolean;
}

class TrialManager {
  private readonly storageKey = 'trial_state';
  private config: TrialConfig;

  constructor(config: TrialConfig) {
    this.config = config;
  }

  /**
   * Start a new trial for a user
   */
  async startTrial(userId: string): Promise<TrialState> {
    const now = Date.now();
    const trial: TrialState = {
      trialId: this.generateTrialId(),
      startDate: now,
      endDate: now + (this.config.durationDays * 24 * 60 * 60 * 1000),
      featuresUnlocked: this.config.features,
      usesRemaining: this.config.usageLimit,
      converted: false,
    };

    // Save to storage
    await chrome.storage.local.set({
      [this.storageKey]: trial,
    });

    // Track in backend
    await this.trackTrialStart(userId, trial);

    // Show welcome message
    this.showTrialWelcomeMessage(trial);

    return trial;
  }

  /**
   * Check current trial status
   */
  async checkTrialStatus(): Promise<TrialStatus> {
    const stored = await chrome.storage.local.get(this.storageKey);
    const trial: TrialState | null = stored[this.storageKey];

    if (!trial) {
      return { isActive: false, reason: 'no_trial' };
    }

    const now = Date.now();

    // Check if trial has expired
    if (now >= trial.endDate) {
      if (trial.converted) {
        return { isActive: false, reason: 'converted' };
      }
      return { 
        isActive: false, 
        reason: 'expired',
        daysUsed: this.config.durationDays,
      };
    }

    // Check usage limits
    if (trial.usesRemaining !== undefined && trial.usesRemaining <= 0) {
      return { isActive: false, reason: 'usage_exhausted' };
    }

    // Trial is active - return status
    const daysRemaining = Math.ceil(
      (trial.endDate - now) / (1000 * 60 * 60 * 24)
    );

    return {
      isActive: true,
      daysRemaining,
      featuresUnlocked: trial.featuresUnlocked,
      showConversionPrompt: daysRemaining <= 3, // Last 3 days
    };
  }

  /**
   * Use one trial allocation (if limited)
   */
  async recordUsage(): Promise<boolean> {
    const stored = await chrome.storage.local.get(this.storageKey);
    const trial: TrialState | null = stored[this.storageKey];

    if (!trial || !trial.usesRemaining) {
      return true; // Unlimited trial
    }

    if (trial.usesRemaining <= 0) {
      return false; // Limit exhausted
    }

    trial.usesRemaining--;
    await chrome.storage.local.set({ [this.storageKey]: trial });

    return true;
  }

  /**
   * Convert trial to paid subscription
   */
  async convertToPaid(userId: string, tier: SubscriptionTier): Promise<void> {
    const stored = await chrome.storage.local.get(this.storageKey);
    const trial: TrialState | null = stored[this.storageKey];

    if (!trial) {
      throw new Error('No active trial to convert');
    }

    // Mark trial as converted
    trial.converted = true;
    await chrome.storage.local.set({ [this.storageKey]: trial });

    // Clear trial storage (subscription takes over)
    await chrome.storage.local.remove(this.storageKey);

    // Track conversion
    await this.trackConversion(userId, trial);

    // Show success message
    this.showConversionSuccessMessage(tier);
  }

  /**
   * Show conversion prompt to user
   */
  async promptConversion(): Promise<void> {
    const status = await this.checkTrialStatus();

    if (!status.isActive || !status.showConversionPrompt) {
      return;
    }

    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/trial.png',
      title: 'Trial Ending Soon',
      message: `Your trial ends in ${status.daysRemaining} days. ` +
               'Upgrade now to keep your features!',
      priority: 1,
      buttons: [
        { title: 'Upgrade Now' },
        { title: 'Later' },
      ],
    });
  }

  private generateTrialId(): string {
    return `trial_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private async trackTrialStart(
    userId: string, 
    trial: TrialState
  ): Promise<void> {
    await fetch('/api/analytics/trial-start', {
      method: 'POST',
      body: JSON.stringify({ userId, trial }),
    });
  }

  private async trackConversion(
    userId: string, 
    trial: TrialState
  ): Promise<void> {
    await fetch('/api/analytics/trial-conversion', {
      method: 'POST',
      body: JSON.stringify({ 
        userId, 
        trialId: trial.trialId,
        duration: Date.now() - trial.startDate,
      }),
    });
  }

  private showTrialWelcomeMessage(trial: TrialState): void {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/welcome.png',
      title: 'Trial Started!',
      message: `You have ${this.config.durationDays} days to try Pro features.`,
      priority: 1,
    });
  }

  private showConversionSuccessMessage(tier: SubscriptionTier): void {
    chrome.notifications.create({
      type: 'basic',
      iconUrl: 'icons/success.png',
      title: 'Welcome to Pro!',
      message: 'Your subscription is now active. Enjoy unlimited access!',
      priority: 1,
    });
  }
}

interface TrialStatus {
  isActive: boolean;
  reason?: 'no_trial' | 'expired' | 'converted' | 'usage_exhausted';
  daysRemaining?: number;
  daysUsed?: number;
  featuresUnlocked?: string[];
  showConversionPrompt?: boolean;
}
```

This TrialManager handles time-based trials, usage-limited trials, and tracks conversion metrics. Customize the conversion prompt timing based on your trial length—shorter trials (7 days) should prompt conversion earlier than longer ones (30 days).

## Handling Subscription Lifecycle Events

Every subscription moves through predictable states: trial, active, past_due, canceled, and expired. Your system must respond correctly to each transition.

### Stripe Webhook Event Mapping

```typescript
// Map Stripe webhook events to system actions
const SUBSCRIPTION_EVENTS: Record<string, SubscriptionAction> = {
  // Trial events
  'customer.subscription.created': 'ACTIVATE',
  'customer.subscription.trial_will_end': 'NOTIFY_TRIAL_ENDING',
  
  // Active subscription events
  'invoice.paid': 'CONFIRM_PAYMENT',
  'customer.subscription.updated': 'SYNC_SUBSCRIPTION',
  
  // Payment failure events
  'invoice.payment_failed': 'ENTER_GRACE_PERIOD',
  'customer.subscription.deleted': 'SCHEDULE_DEACTIVATION',
  
  // Cancellation events
  'customer.subscription.canceled': 'SCHEDULE_DEACTIVATION',
};

interface SubscriptionAction {
  event: string;
  handler: (data: StripeWebhookData) => Promise<void>;
}

async function handleWebhookEvent(event: StripeWebhookData): Promise<void> {
  const eventType = event.type;
  const action = SUBSCRIPTION_EVENTS[eventType];
  
  if (!action) {
    console.log(`Unhandled webhook event: ${eventType}`);
    return;
  }

  try {
    switch (eventType) {
      case 'customer.subscription.created':
        await activateSubscription(event.data.object);
        break;
        
      case 'invoice.paid':
        await confirmPayment(event.data.object);
        break;
        
      case 'invoice.payment_failed':
        await handlePaymentFailure(event.data.object);
        break;
        
      case 'customer.subscription.updated':
        await syncSubscription(event.data.object);
        break;
        
      case 'customer.subscription.canceled':
      case 'customer.subscription.deleted':
        await scheduleDeactivation(event.data.object);
        break;
        
      case 'customer.subscription.trial_will_end':
        await notifyTrialEnding(event.data.object);
        break;
    }
  } catch (error) {
    console.error(`Error handling ${eventType}:`, error);
    // Stripe will retry webhook on 5xx errors
    throw error;
  }
}

/**
 * Activate new subscription - immediate feature access
 */
async function activateSubscription(subscription: StripeSubscription): Promise<void> {
  const userId = subscription.metadata.userId;
  const tier = mapStripePriceToTier(subscription.items.data[0].price.id);
  
  await updateLicense(userId, {
    tier,
    validUntil: subscription.current_period_end * 1000,
    status: 'active',
    stripeSubscriptionId: subscription.id,
  });
  
  await notifyExtensionLicenseUpdate(userId);
}

/**
 * Confirm payment - extend subscription period
 */
async function confirmPayment(invoice: StripeInvoice): Promise<void> {
  const subscription = invoice.subscription as string;
  
  await extendLicensePeriod(subscription, invoice.period_end * 1000);
  
  // Clear any grace period
  await clearGracePeriod(invoice.customer);
}

/**
 * Handle payment failure - enter grace period
 */
async function handlePaymentFailure(invoice: StripeInvoice): Promise<void> {
  const subscription = invoice.subscription as StripeSubscription;
  const gracePeriodEnd = Date.now() + (7 * 24 * 60 * 60 * 1000);
  
  await setGracePeriod(subscription.metadata.userId, gracePeriodEnd);
  
  await sendEmail(subscription.metadata.userId, 'payment_failed', {
    gracePeriodDays: 7,
    amount: invoice.amount_due / 100,
  });
  
  await notifyExtensionPaymentFailed(subscription.metadata.userId);
}

/**
 * Sync subscription changes (upgrade/downgrade)
 */
async function syncSubscription(subscription: StripeSubscription): Promise<void> {
  const userId = subscription.metadata.userId;
  const newTier = mapStripePriceToTier(subscription.items.data[0].price.id);
  
  // Check if upgrade or downgrade
  const currentLicense = await getLicense(userId);
  
  if (getTierLevel(newTier) > getTierLevel(currentLicense.tier)) {
    // Upgrade - immediate effect
    await updateLicense(userId, { tier: newTier });
    await notifyExtensionLicenseUpdate(userId);
  } else {
    // Downgrade - effect at period end
    await scheduleTierChange(userId, newTier, subscription.current_period_end * 1000);
  }
}

/**
 * Schedule deactivation after cancellation
 */
async function scheduleDeactivation(subscription: StripeSubscription): Promise<void> {
  const userId = subscription.metadata.userId;
  const accessUntil = subscription.current_period_end * 1000;
  
  await scheduleLicenseExpiry(userId, accessUntil);
  
  await sendEmail(userId, 'subscription_canceled', {
    accessUntil: new Date(accessUntil).toLocaleDateString(),
  });
}

/**
 * Notify user trial is ending
 */
async function notifyTrialEnding(subscription: StripeSubscription): Promise<void> {
  const userId = subscription.metadata.userId;
  const daysRemaining = Math.ceil(
    (subscription.trial_end! * 1000 - Date.now()) / (1000 * 60 * 60 * 24)
  );
  
  await sendEmail(userId, 'trial_ending', { daysRemaining });
  
  // Also notify in-extension
  await notifyExtensionTrialEnding(userId, daysRemaining);
}

function mapStripePriceToTier(priceId: string): SubscriptionTier {
  const priceTierMap: Record<string, SubscriptionTier> = {
    'price_basic_monthly': SubscriptionTier.BASIC,
    'price_pro_monthly': SubscriptionTier.PRO,
    'price_enterprise_monthly': SubscriptionTier.ENTERPRISE,
  };
  
  return priceTierMap[priceId] || SubscriptionTier.FREE;
}

function getTierLevel(tier: SubscriptionTier): number {
  const levels: Record<SubscriptionTier, number> = {
    [SubscriptionTier.FREE]: 0,
    [SubscriptionTier.BASIC]: 1,
    [SubscriptionTier.PRO]: 2,
    [SubscriptionTier.ENTERPRISE]: 3,
  };
  return levels[tier];
}
```

This webhook handler covers all major lifecycle transitions. The key principle: upgrades take effect immediately, while downgrades and cancellations take effect at the period end.

## Metrics and Analytics

Understanding your subscription metrics is essential for making data-driven decisions about pricing, product development, and marketing spend.

### SubscriptionMetrics Dashboard

```typescript
interface SubscriptionMetrics {
  // Current state
  totalSubscribers: number;
  mrr: number; // Monthly Recurring Revenue
  arr: number; // Annual Recurring Revenue
  
  // Growth metrics
  newSubscribersThisMonth: number;
  mrrGrowthRate: number;
  
  // Retention metrics
  churnRate: number;
  churnedMRR: number;
  netRevenueRetention: number;
  
  // Financial metrics
  averageLTV: number;
  cac: number;
  ltvToCACRatio: number;
  
  // Tier breakdown
  tierDistribution: Record<SubscriptionTier, number>;
}

class SubscriptionMetricsAggregator {
  private readonly analyticsEndpoint: string;

  constructor(analyticsEndpoint: string) {
    this.analyticsEndpoint = analyticsEndpoint;
  }

  /**
   * Calculate complete metrics dashboard
   */
  async calculateDashboard(): Promise<SubscriptionMetrics> {
    const [revenue, subscribers, cohorts] = await Promise.all([
      this.getRevenueData(),
      this.getSubscriberData(),
      this.getCohortData(),
    ]);

    const mrr = this.calculateMRR(revenue);
    const churnRate = this.calculateChurnRate(subscribers);
    const averageLTV = this.calculateLTV(revenue, churnRate);

    return {
      totalSubscribers: subscribers.length,
      mrr,
      arr: mrr * 12,
      newSubscribersThisMonth: this.getNewSubscribers(subscribers),
      mrrGrowthRate: this.calculateMRRGrowth(revenue),
      churnRate,
      churnedMRR: this.calculateChurnedMRR(revenue),
      netRevenueRetention: this.calculateNRR(revenue),
      averageLTV,
      cac: await this.getCAC(),
      ltvToCACRatio: averageLTV / (await this.getCAC()),
      tierDistribution: this.getTierDistribution(subscribers),
    };
  }

  /**
   * Calculate Monthly Recurring Revenue
   */
  private calculateMRR(revenueData: RevenueRecord[]): number {
    return revenueData
      .filter(r => r.status === 'active')
      .reduce((sum, r) => sum + r.monthlyAmount, 0);
  }

  /**
   * Calculate churn rate (monthly %)
   * Formula: Churned customers / Customers at start of month
   */
  private calculateChurnRate(subscribers: SubscriberRecord[]): number {
    const now = new Date();
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
    
    const startOfMonthCount = subscribers.filter(
      s => s.createdAt < monthStart.getTime()
    ).length;
    
    const churnedThisMonth = subscribers.filter(
      s => s.canceledAt && s.canceledAt >= monthStart.getTime()
    ).length;

    if (startOfMonthCount === 0) return 0;
    
    return (churnedThisMonth / startOfMonthCount) * 100;
  }

  /**
   * Calculate Lifetime Value
   * Formula: ARPU / Churn Rate
   */
  private calculateLTV(revenueData: RevenueRecord[], churnRate: number): number {
    if (churnRate === 0) return 0;
    
    const totalMRR = this.calculateMRR(revenueData);
    const activeSubscribers = revenueData.filter(r => r.status === 'active').length;
    const arpu = activeSubscribers > 0 ? totalMRR / activeSubscribers : 0;
    
    return arpu / (churnRate / 100);
  }

  /**
   * Calculate MRR growth rate
   */
  private calculateMRRGrowth(revenueData: RevenueRecord[]): number {
    const now = Date.now();
    const thirtyDaysAgo = now - (30 * 24 * 60 * 60 * 1000);
    const sixtyDaysAgo = now - (60 * 24 * 60 * 60 * 1000);

    const currentMRR = revenueData
      .filter(r => r.date >= thirtyDaysAgo)
      .reduce((sum, r) => sum + r.monthlyAmount, 0);

    const previousMRR = revenueData
      .filter(r => r.date >= sixtyDaysAgo && r.date < thirtyDaysAgo)
      .reduce((sum, r) => sum + r.monthlyAmount, 0);

    if (previousMRR === 0) return currentMRR > 0 ? 100 : 0;
    
    return ((currentMRR - previousMRR) / previousMRR) * 100;
  }

  /**
   * Calculate Net Revenue Retention
   * Should be >100% if existing customers are upgrading
   */
  private calculateNRR(revenueData: RevenueRecord[]): number {
    const now = Date.now();
    const thirtyDaysAgo = now - (30 * 24 * 60 * 60 * 1000);

    const mrrStart = revenueData
      .filter(r => r.date >= thirtyDaysAgo)
      .reduce((sum, r) => sum + r.startOfPeriodAmount, 0);

    const mrrEnd = revenueData
      .filter(r => r.date >= thirtyDaysAgo)
      .reduce((sum, r) => sum + r.endOfPeriodAmount, 0);

    if (mrrStart === 0) return 100;
    
    return (mrrEnd / mrrStart) * 100;
  }

  /**
   * Get Customer Acquisition Cost
   * Total marketing spend / New customers acquired
   */
  async getCAC(): Promise<number> {
    const [marketingSpend, newCustomers] = await Promise.all([
      this.getMarketingSpend(),
      this.getNewCustomersThisMonth(),
    ]);

    return newCustomers > 0 ? marketingSpend / newCustomers : 0;
  }

  /**
   * Determine if churn is problematic
   * >5% monthly churn is a red flag requiring immediate attention
   */
  async isChurnProblematic(): Promise<boolean> {
    const metrics = await this.calculateDashboard();
    return metrics.churnRate > 5;
  }

  private async getRevenueData(): Promise<RevenueRecord[]> {
    const response = await fetch(`${this.analyticsEndpoint}/revenue`);
    return response.json();
  }

  private async getSubscriberData(): Promise<SubscriberRecord[]> {
    const response = await fetch(`${this.analyticsEndpoint}/subscribers`);
    return response.json();
  }

  private async getCohortData(): Promise<CohortRecord[]> {
    const response = await fetch(`${this.analyticsEndpoint}/cohorts`);
    return response.json();
  }

  private async getMarketingSpend(): Promise<number> {
    const response = await fetch(`${this.analyticsEndpoint}/marketing-spend`);
    const data = await response.json();
    return data.total;
  }

  private async getNewCustomersThisMonth(): Promise<number> {
    const response = await fetch(`${this.analyticsEndpoint}/new-customers`);
    const data = await response.json();
    return data.count;
  }

  private getNewSubscribers(subscribers: SubscriberRecord[]): number {
    const now = new Date();
    const monthStart = new Date(now.getFullYear(), now.getMonth(), 1);
    
    return subscribers.filter(s => s.createdAt >= monthStart.getTime()).length;
  }

  private getTierDistribution(
    subscribers: SubscriberRecord[]
  ): Record<SubscriptionTier, number> {
    const distribution: Record<SubscriptionTier, number> = {
      [SubscriptionTier.FREE]: 0,
      [SubscriptionTier.BASIC]: 0,
      [SubscriptionTier.PRO]: 0,
      [SubscriptionTier.ENTERPRISE]: 0,
    };

    subscribers.forEach(s => {
      distribution[s.tier]++;
    });

    return distribution;
  }
}

interface RevenueRecord {
  date: number;
  monthlyAmount: number;
  startOfPeriodAmount: number;
  endOfPeriodAmount: number;
  status: string;
}

interface SubscriberRecord {
  id: string;
  tier: SubscriptionTier;
  createdAt: number;
  canceledAt?: number;
}

interface CohortRecord {
  cohortMonth: string;
  retentionByMonth: number[];
}
```

Track these metrics weekly and set alerts for concerning trends. A churn rate above 5% monthly requires immediate investigation—it's often a sign of product issues, pricing problems, or poor onboarding.

## Pricing Strategy

Setting subscription prices requires balancing value delivery, market positioning, and willingness to pay. The most effective approach combines value-based pricing with competitive analysis and iterative testing.

### Pricing Framework

**Value-Based Pricing**: Calculate the value your extension delivers and price at 10-25% of that value. If your extension saves users 10 hours monthly at $30/hour value ($300 monthly value), a $5-15/month subscription feels like a bargain. Make the value calculation explicit in your marketing—show users exactly what they're getting.

**Competitive Analysis**: Research similar extensions in your category. Price 20-30% below established competitors when launching, then raise prices as you build brand recognition. Never compete solely on price; compete on value.

**Annual Discounts**: Offer 20-30% off for annual billing (e.g., $49.99/year vs $4.99/month). This aligns with your interest in retention while giving price-sensitive users a better deal.

**Price Testing**: Implement A/B tests with different price points. Show different prices to different user segments and measure conversion rates. Even small price changes (from $4.99 to $5.99) can significantly impact revenue.

For deeper pricing strategy guidance, see [Pricing Strategies](articles/pricing-strategies.md).

---

Built by [Zovo](https://zovo.one) - Open-source tools and guides for extension developers.
