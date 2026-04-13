"""
Expense Tracker — Analytics Engine
Data analysis, insights generation, and budget tracking.
"""

from datetime import datetime, timedelta
from config import CURRENCY_SYMBOL, DATE_FORMAT


def get_insights(db):
    """Generate a list of insight strings based on spending data."""
    insights = []

    total = db.get_total()
    if total == 0:
        return ["📊 Start adding expenses to unlock personalized insights!"]

    # Top category
    breakdown = db.get_category_breakdown()
    if breakdown:
        top = breakdown[0]
        pct = (top["total"] / total) * 100 if total > 0 else 0
        insights.append(
            f"🏆 Your top spending category is {top['category']} "
            f"({pct:.0f}% — {CURRENCY_SYMBOL}{top['total']:,.2f})"
        )

    # This week vs last week
    weekly = db.get_weekly_trend(2)
    if len(weekly) >= 2 and weekly[0]["total"] > 0:
        last_week = weekly[0]["total"]
        this_week = weekly[1]["total"]

        if last_week > 0:
            change = ((this_week - last_week) / last_week) * 100
            if change > 0:
                insights.append(
                    f"📈 You spent {change:.0f}% more this week vs last week "
                    f"({CURRENCY_SYMBOL}{this_week:,.0f} vs {CURRENCY_SYMBOL}{last_week:,.0f})"
                )
            elif change < 0:
                insights.append(
                    f"📉 You spent {abs(change):.0f}% less this week vs last week — nice! "
                    f"({CURRENCY_SYMBOL}{this_week:,.0f} vs {CURRENCY_SYMBOL}{last_week:,.0f})"
                )
            else:
                insights.append(
                    f"➡️ Your spending is the same as last week ({CURRENCY_SYMBOL}{this_week:,.0f})"
                )

    # Average daily spend this month
    monthly_total = db.get_monthly_total()
    today = datetime.now()
    days_in_month = today.day
    if days_in_month > 0 and monthly_total > 0:
        avg = monthly_total / days_in_month
        insights.append(
            f"📅 Your average daily spend this month is {CURRENCY_SYMBOL}{avg:,.2f}"
        )

    # Total expense count
    count = db.get_expense_count()
    insights.append(f"📋 You have {count} total expenses tracked")

    # Average expense amount
    if count > 0:
        avg_amount = total / count
        insights.append(
            f"💳 Your average expense is {CURRENCY_SYMBOL}{avg_amount:,.2f}"
        )

    # Number of categories used
    if breakdown:
        insights.append(
            f"🏷️ You spend across {len(breakdown)} categories"
        )

    return insights


def get_budget_status(db, budget):
    """Get budget usage percentage and warning level."""
    if budget <= 0:
        return {"percentage": 0, "level": "none", "remaining": 0}

    monthly_total = db.get_monthly_total()
    pct = (monthly_total / budget) * 100
    remaining = budget - monthly_total

    if pct >= 100:
        level = "exceeded"
    elif pct >= 80:
        level = "warning"
    elif pct >= 50:
        level = "caution"
    else:
        level = "safe"

    return {
        "percentage": pct,
        "level": level,
        "remaining": remaining,
        "spent": monthly_total,
        "budget": budget,
    }


def get_spending_velocity(db):
    """Compare daily spending rate: this month vs last month."""
    today = datetime.now()

    # This month
    this_month_total = db.get_monthly_total()
    days_this_month = today.day

    # Last month (approximate)
    last_month_start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
    last_month_end = today.replace(day=1) - timedelta(days=1)

    cursor = db.conn.cursor()
    cursor.execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM expenses WHERE date >= ? AND date <= ?",
        (last_month_start.strftime(DATE_FORMAT), last_month_end.strftime(DATE_FORMAT)),
    )
    last_month_total = cursor.fetchone()["total"]
    days_last_month = last_month_end.day

    this_rate = this_month_total / max(days_this_month, 1)
    last_rate = last_month_total / max(days_last_month, 1)

    # Calculate change percentage safely
    if last_rate > 0:
        change_pct = ((this_rate - last_rate) / last_rate) * 100
    else:
        change_pct = 100 if this_rate > 0 else 0

    return {
        "this_month_rate": this_rate,
        "last_month_rate": last_rate,
        "change_pct": change_pct,
    }