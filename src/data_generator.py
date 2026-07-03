"""
Synthetic E-Commerce Customer Dataset Generator
------------------------------------------------
Produces a realistic customer table with RFM-style behavioural fields
plus engagement/support signals, and a churn label that is causally
linked to those fields (not random) so the ML models downstream have
real signal to learn from.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


def generate_customers(n_customers: int = 2000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    today = datetime(2026, 7, 1)

    customer_id = [f"CUST-{100000 + i}" for i in range(n_customers)]
    age = rng.integers(18, 75, n_customers)
    gender = rng.choice(["Female", "Male", "Other"], n_customers, p=[0.49, 0.48, 0.03])

    # Tenure: how long they've been a customer (days)
    tenure_days = rng.integers(30, 2000, n_customers)
    signup_date = [today - timedelta(days=int(t)) for t in tenure_days]

    # Underlying "engagement quality" latent variable drives everything else
    engagement = rng.beta(2, 2, n_customers)  # 0..1, roughly bell-shaped

    # Frequency: orders in the last 12 months, tied to engagement + tenure
    frequency = np.clip(
        rng.poisson(lam=2 + engagement * 18) * (tenure_days > 60), 0, None
    )

    # Recency: days since last purchase — inversely tied to engagement
    recency_days = np.clip(
        (rng.exponential(scale=40, size=n_customers) * (1.3 - engagement)).astype(int),
        1, 730
    )

    # Average order value — some customers are just higher spenders regardless of engagement
    base_aov = rng.gamma(shape=3, scale=15, size=n_customers) + 10
    avg_order_value = np.round(base_aov, 2)

    monetary = np.round(frequency * avg_order_value * rng.uniform(0.85, 1.15, n_customers), 2)

    num_categories_purchased = np.clip(rng.poisson(lam=1 + engagement * 5), 1, 12)

    # Returns: higher for low-engagement / dissatisfied customers
    dissatisfaction = 1 - engagement
    num_returns = rng.poisson(lam=0.3 + dissatisfaction * 2.5 + 0.05 * frequency)
    return_rate = np.round(
        np.where(frequency > 0, np.clip(num_returns / np.maximum(frequency, 1), 0, 1), 0), 3
    )

    support_tickets = rng.poisson(lam=0.2 + dissatisfaction * 3)
    avg_satisfaction_score = np.clip(
        np.round(5 - dissatisfaction * 4 + rng.normal(0, 0.6, n_customers), 1), 1, 5
    )

    email_open_rate = np.round(np.clip(engagement + rng.normal(0, 0.12, n_customers), 0, 1), 3)
    discount_usage_rate = np.round(np.clip(dissatisfaction * 0.6 + rng.normal(0, 0.15, n_customers), 0, 1), 3)

    preferred_channel = rng.choice(["Mobile App", "Website", "In-Store"], n_customers, p=[0.5, 0.4, 0.1])
    loyalty_member = rng.choice([1, 0], n_customers, p=[0.35, 0.65])

    # --- Churn label: logistic combination of recency, frequency, satisfaction, tickets ---
    z = (
        0.045 * recency_days
        - 0.32 * frequency
        - 0.9 * avg_satisfaction_score
        + 0.55 * support_tickets
        + 2.1 * return_rate
        - 1.4 * loyalty_member
        - 0.015 * (tenure_days / 30)
        + rng.normal(0, 1.1, n_customers)
    )
    churn_prob = 1 / (1 + np.exp(-(z - 2.0) * 0.6))
    churned = (rng.uniform(0, 1, n_customers) < churn_prob).astype(int)

    df = pd.DataFrame({
        "customer_id": customer_id,
        "age": age,
        "gender": gender,
        "signup_date": [d.strftime("%Y-%m-%d") for d in signup_date],
        "tenure_days": tenure_days,
        "recency_days": recency_days,
        "frequency": frequency,
        "monetary": monetary,
        "avg_order_value": avg_order_value,
        "num_categories_purchased": num_categories_purchased,
        "num_returns": num_returns,
        "return_rate": return_rate,
        "support_tickets": support_tickets,
        "avg_satisfaction_score": avg_satisfaction_score,
        "email_open_rate": email_open_rate,
        "discount_usage_rate": discount_usage_rate,
        "preferred_channel": preferred_channel,
        "loyalty_member": loyalty_member,
        "churned": churned,
    })

    return df


if __name__ == "__main__":
    df = generate_customers(2000)
    out_path = "data/sample_customers.csv"
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} customers -> {out_path}")
    print(f"Churn rate: {df['churned'].mean():.1%}")
    print(df.describe(include='all').T[["mean", "std", "min", "max"]].head(10))
