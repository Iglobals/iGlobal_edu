"""
Seeds/updates the subscription_plans table and creates the matching
recurring Plans on Paystack.

Run the new Alembic migration first (flask db upgrade). Prices below are
placeholders - no price was specified for iGlobal_edu's Pro plan yet, so
they're deliberately editable here and in the DB, not hardcoded elsewhere.
Change PRICING_NGN and re-run to update (existing rows are upserted by name,
Paystack plans are created once and then reused).

Usage:
    python seed_subscription_plans.py
"""
from app import app, db
from models import SubscriptionPlan
import paystack_client

# Placeholder - not yet decided. Edit and re-run, or just edit the row(s)
# directly in subscription_plans afterward.
PRICING_NGN = {
    "monthly": 3000,
    "annual": 30000,  # 2 months free vs. paying monthly all year - adjust freely
}

PAYSTACK_INTERVAL = {"monthly": "monthly", "annual": "annually"}


def upsert_plan(interval, price_ngn, paystack_plan_code):
    name = f"Pro {interval.capitalize()}"
    plan = SubscriptionPlan.query.filter_by(name=name).first()
    if plan is None:
        plan = SubscriptionPlan(name=name)
    plan.interval = interval
    plan.price_ngn = price_ngn
    plan.price_usd = None  # no USD pricing needed here yet - NGN only, unlike iTest
    plan.paystack_plan_code = paystack_plan_code
    plan.is_active = True
    db.session.add(plan)
    return plan


def get_or_create_paystack_plan(interval, amount_ngn):
    name = f"Pro {interval.capitalize()}"
    existing = SubscriptionPlan.query.filter_by(name=name).first()
    if existing and existing.paystack_plan_code:
        print(f"  {name}: reusing existing Paystack plan {existing.paystack_plan_code}")
        return existing.paystack_plan_code

    data = paystack_client.create_plan(
        name=name,
        amount_kobo=int(amount_ngn * 100),
        interval=PAYSTACK_INTERVAL[interval],
    )
    print(f"  {name}: created Paystack plan {data['plan_code']}")
    return data["plan_code"]


def main():
    with app.app_context():
        for interval, price_ngn in PRICING_NGN.items():
            print(f"--- Pro {interval} ---")
            plan_code = get_or_create_paystack_plan(interval, price_ngn)
            upsert_plan(interval, price_ngn, plan_code)

        db.session.commit()
        print("\nDone. subscription_plans is seeded.")


if __name__ == '__main__':
    main()
