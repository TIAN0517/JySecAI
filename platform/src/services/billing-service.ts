import Stripe from "stripe";

import type { AppConfig } from "../config.js";
import { DomainError } from "../core/errors.js";
import type { ControlPlaneStore } from "../core/store.js";
import { planIdSchema, type ActorContext, type PlanId, type TenantSubscription } from "../core/types.js";

export class BillingService {
  readonly #stripe: Stripe | null;
  readonly #webhookSecret: string | undefined;
  readonly #baseUrl: string;
  readonly #store: ControlPlaneStore;
  readonly #priceIds: Partial<Record<PlanId, string>>;

  constructor(config: AppConfig, store: ControlPlaneStore) {
    this.#stripe = config.stripe.secretKey ? new Stripe(config.stripe.secretKey) : null;
    this.#webhookSecret = config.stripe.webhookSecret;
    this.#baseUrl = config.publicBaseUrl.replace(/\/$/u, "");
    this.#store = store;
    this.#priceIds = {
      ...(config.stripe.professionalPriceId ? { professional: config.stripe.professionalPriceId } : {}),
      ...(config.stripe.businessPriceId ? { business: config.stripe.businessPriceId } : {}),
    };
  }

  get enabled(): boolean {
    return this.#stripe !== null;
  }

  async createCheckout(actor: ActorContext, planId: PlanId): Promise<{ url: string }> {
    this.#assertBillingAdmin(actor);
    const stripe = this.#requireStripe();
    if (!(["professional", "business"] as PlanId[]).includes(planId)) {
      throw new DomainError("plan_not_self_service", "This plan is not available through self-service checkout", 400);
    }
    const price = this.#priceIds[planId];
    if (!price) throw new DomainError("billing_not_configured", `Stripe price is not configured for ${planId}`, 503);

    const current = await this.#store.getSubscription(actor.tenantId);
    const session = await stripe.checkout.sessions.create({
      mode: "subscription",
      line_items: [{ price, quantity: 1 }],
      success_url: `${this.#baseUrl}/?billing=success&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${this.#baseUrl}/?billing=cancelled`,
      client_reference_id: actor.tenantId,
      ...(current?.providerCustomerId
        ? { customer: current.providerCustomerId }
        : actor.email
          ? { customer_email: actor.email }
          : {}),
      allow_promotion_codes: true,
      metadata: { jysec_tenant_id: actor.tenantId, jysec_plan_id: planId },
      subscription_data: {
        metadata: { jysec_tenant_id: actor.tenantId, jysec_plan_id: planId },
      },
    });
    if (!session.url) throw new DomainError("checkout_failed", "Stripe did not return a checkout URL", 502);
    return { url: session.url };
  }

  async createPortal(actor: ActorContext): Promise<{ url: string }> {
    this.#assertBillingAdmin(actor);
    const stripe = this.#requireStripe();
    const subscription = await this.#store.getSubscription(actor.tenantId);
    if (!subscription?.providerCustomerId) {
      throw new DomainError("billing_customer_missing", "No billing customer is linked to this tenant", 404);
    }
    const session = await stripe.billingPortal.sessions.create({
      customer: subscription.providerCustomerId,
      return_url: this.#baseUrl,
    });
    return { url: session.url };
  }

  async handleWebhook(rawBody: Buffer, signature: string): Promise<{ received: true }> {
    const stripe = this.#requireStripe();
    if (!this.#webhookSecret) {
      throw new DomainError("billing_not_configured", "Stripe webhook verification is not configured", 503);
    }
    let event: Stripe.Event;
    try {
      event = stripe.webhooks.constructEvent(rawBody, signature, this.#webhookSecret);
    } catch {
      throw new DomainError("invalid_webhook_signature", "Stripe webhook signature is invalid", 400);
    }

    if (
      event.type === "customer.subscription.created" ||
      event.type === "customer.subscription.updated" ||
      event.type === "customer.subscription.deleted"
    ) {
      const subscription = event.data.object;
      const tenantId = subscription.metadata.jysec_tenant_id?.trim();
      const parsedPlan = planIdSchema.safeParse(subscription.metadata.jysec_plan_id);
      if (!tenantId || !parsedPlan.success) {
        throw new DomainError("invalid_subscription_metadata", "Stripe subscription metadata is incomplete", 400);
      }
      const customerId =
        typeof subscription.customer === "string" ? subscription.customer : subscription.customer.id;
      const periodEnd = subscription.items.data
        .map((item) => item.current_period_end)
        .filter((value): value is number => typeof value === "number")
        .sort((left, right) => right - left)[0];
      const record: TenantSubscription = {
        tenantId,
        planId: parsedPlan.data,
        provider: "stripe",
        providerCustomerId: customerId,
        providerSubscriptionId: subscription.id,
        status: subscription.status,
        ...(periodEnd !== undefined ? { currentPeriodEnd: new Date(periodEnd * 1000).toISOString() } : {}),
        updatedAt: new Date().toISOString(),
      };
      await this.#store.upsertSubscription(record);
    }
    return { received: true };
  }

  #requireStripe(): Stripe {
    if (!this.#stripe) throw new DomainError("billing_not_configured", "Stripe billing is not configured", 503);
    return this.#stripe;
  }

  #assertBillingAdmin(actor: ActorContext): void {
    if (!actor.roles.some((role) => role === "owner" || role === "admin")) {
      throw new DomainError("billing_admin_required", "An owner or administrator role is required", 403);
    }
  }
}
