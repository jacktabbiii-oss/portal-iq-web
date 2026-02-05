import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";
import PocketBase from "pocketbase";

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: "2023-10-16",
});

const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET!;

// Initialize PocketBase
const pb = new PocketBase(process.env.NEXT_PUBLIC_POCKETBASE_URL);

export async function POST(request: NextRequest) {
  try {
    const body = await request.text();
    const signature = request.headers.get("stripe-signature");

    if (!signature) {
      return NextResponse.json(
        { error: "Missing stripe-signature header" },
        { status: 400 }
      );
    }

    // Verify webhook signature
    let event: Stripe.Event;
    try {
      event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
    } catch (err) {
      console.error("Webhook signature verification failed:", err);
      return NextResponse.json(
        { error: "Invalid signature" },
        { status: 400 }
      );
    }

    // Handle the event
    switch (event.type) {
      case "checkout.session.completed": {
        const session = event.data.object as Stripe.Checkout.Session;
        await handleCheckoutCompleted(session);
        break;
      }

      case "customer.subscription.created":
      case "customer.subscription.updated": {
        const subscription = event.data.object as Stripe.Subscription;
        await handleSubscriptionUpdated(subscription);
        break;
      }

      case "customer.subscription.deleted": {
        const subscription = event.data.object as Stripe.Subscription;
        await handleSubscriptionCancelled(subscription);
        break;
      }

      case "invoice.payment_failed": {
        const invoice = event.data.object as Stripe.Invoice;
        await handlePaymentFailed(invoice);
        break;
      }

      default:
        console.log(`Unhandled event type: ${event.type}`);
    }

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error("Webhook error:", error);
    return NextResponse.json(
      { error: "Webhook handler failed" },
      { status: 500 }
    );
  }
}

async function handleCheckoutCompleted(session: Stripe.Checkout.Session) {
  const customerEmail = session.customer_email;
  const customerId = session.customer as string;
  const subscriptionId = session.subscription as string;

  if (!customerEmail) {
    console.error("No customer email in checkout session");
    return;
  }

  try {
    // Find user by email in PocketBase
    const users = await pb.collection("users").getList(1, 1, {
      filter: `email = "${customerEmail}"`,
    });

    if (users.items.length === 0) {
      console.log(`User not found for email: ${customerEmail}`);
      // User doesn't exist yet - they'll need to register
      // Store the subscription info for later linking
      return;
    }

    const user = users.items[0];

    // Update user with Stripe info
    await pb.collection("users").update(user.id, {
      stripe_customer_id: customerId,
      subscription: "pro",
      subscription_status: "trialing", // 14-day trial
    });

    console.log(`Updated user ${customerEmail} with Stripe subscription`);
  } catch (error) {
    console.error("Error updating user after checkout:", error);
  }
}

async function handleSubscriptionUpdated(subscription: Stripe.Subscription) {
  const customerId = subscription.customer as string;

  // Map Stripe status to our status
  const statusMap: Record<string, string> = {
    active: "active",
    trialing: "trialing",
    past_due: "past_due",
    canceled: "canceled",
    unpaid: "past_due",
  };

  const subscriptionStatus = statusMap[subscription.status] || subscription.status;

  try {
    // Find user by Stripe customer ID
    const users = await pb.collection("users").getList(1, 1, {
      filter: `stripe_customer_id = "${customerId}"`,
    });

    if (users.items.length === 0) {
      console.log(`No user found for Stripe customer: ${customerId}`);
      return;
    }

    const user = users.items[0];

    // Update subscription status
    await pb.collection("users").update(user.id, {
      subscription_status: subscriptionStatus,
      subscription_end: subscription.current_period_end
        ? new Date(subscription.current_period_end * 1000).toISOString()
        : null,
    });

    console.log(`Updated subscription status for user ${user.email}: ${subscriptionStatus}`);
  } catch (error) {
    console.error("Error updating subscription:", error);
  }
}

async function handleSubscriptionCancelled(subscription: Stripe.Subscription) {
  const customerId = subscription.customer as string;

  try {
    const users = await pb.collection("users").getList(1, 1, {
      filter: `stripe_customer_id = "${customerId}"`,
    });

    if (users.items.length === 0) {
      return;
    }

    const user = users.items[0];

    await pb.collection("users").update(user.id, {
      subscription: "free",
      subscription_status: "canceled",
    });

    console.log(`Subscription cancelled for user ${user.email}`);
  } catch (error) {
    console.error("Error handling subscription cancellation:", error);
  }
}

async function handlePaymentFailed(invoice: Stripe.Invoice) {
  const customerId = invoice.customer as string;

  try {
    const users = await pb.collection("users").getList(1, 1, {
      filter: `stripe_customer_id = "${customerId}"`,
    });

    if (users.items.length === 0) {
      return;
    }

    const user = users.items[0];

    await pb.collection("users").update(user.id, {
      subscription_status: "past_due",
    });

    console.log(`Payment failed for user ${user.email}`);
    // TODO: Send email notification about failed payment
  } catch (error) {
    console.error("Error handling payment failure:", error);
  }
}
