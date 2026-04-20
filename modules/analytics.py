"""
Expense Tracker — Analytics Engine
Data analysis, insights generation, and budget tracking.
"""

from datetime import datetime, timedelta
from config import CURRENCY_SYMBOL, DATE_FORMAT


def get_insights(db):
    """Generate meaningful, human-readable insights as structured data."""
    insights = []

    total = db.get_total()
    if total == 0:
        return [{
            "icon": "📊", 
            "title": "No Data Yet", 
            "message": "Start adding expenses to unlock personalized insights!"
        }]

    # 1. Largest Expense
    largest = db.get_largest_expense()
    if largest and largest["amount"] > 0:
        cat = largest["category"]
        amt = largest["amount"]
        insights.append({
            "icon": "💳", 
            "title": "Largest Single Expense", 
            "message": f"Your largest expense was {CURRENCY_SYMBOL}{amt:,.0f} on {cat}. Reviewing big-ticket items helps you prioritize future spending."
        })

    # 2. Week-on-week comparison
    this_week = db.get_weekly_total()
    last_week = db.get_last_week_total()
    if last_week > 0:
        change_pct = ((this_week - last_week) / last_week) * 100
        if change_pct > 15:
            msg = f"Your spending increased by {change_pct:.0f}% compared to last week. Taking a moment before buying can help bring this back down."
            insights.append({"icon": "📈", "title": "Spending is Up", "message": msg})
        elif change_pct < -15:
            msg = f"Your spending decreased by {abs(change_pct):.0f}% compared to last week. Great job holding onto your cash!"
            insights.append({"icon": "📉", "title": "Spending is Down", "message": msg})
        else:
            msg = "Your spending is nearly identical to last week. You've established a stable financial routine."
            insights.append({"icon": "⚖️", "title": "Consistent Routine", "message": msg})

    # 3. Peak spending day
    peak_day = db.get_peak_spending_day()
    if peak_day and peak_day["total"] > 0:
        try:
            from datetime import datetime
            from config import DATE_FORMAT
            d = datetime.strptime(peak_day["date"], DATE_FORMAT)
            display_date = d.strftime("%d %b %Y")
        except Exception:
            display_date = peak_day["date"]
            
        amt = peak_day["total"]
        insights.append({
            "icon": "📅", 
            "title": "Peak Spending Day", 
            "message": f"Your highest spending day was {display_date} with {CURRENCY_SYMBOL}{amt:,.0f}. Spreading out purchases can make your budget feel less strained."
        })

    # 4. Weekend vs Weekday
    try:
        avg_data = db.get_weekend_vs_weekday_avg()
        we_avg = avg_data.get("weekend_avg", 0)
        wd_avg = avg_data.get("weekday_avg", 0)
        
        if we_avg > 0 and wd_avg > 0:
            if we_avg > wd_avg * 1.5:
                insights.append({
                    "icon": "🎉", 
                    "title": "Weekend Spender", 
                    "message": "You spend significantly more on weekends compared to weekdays. Planning weekend activities in advance might help you save."
                })
            elif wd_avg > we_avg * 1.5:
                insights.append({
                    "icon": "💼", 
                    "title": "Weekday Spender", 
                    "message": "Your weekday spending is higher than on weekends. Consider packing lunches or making coffee at home to cut daily costs."
                })
    except Exception:
        pass

    # Limit to 4-5 high quality insights
    return insights[:5]


def get_weekly_summary(db):
    """
    Return a dict with key weekly metrics for the insights panel.
    Keys:
        this_week   – total spent this week
        last_week   – total spent last week
        change_pct  – % change (positive = up, negative = down)
        top_cat     – dict with 'category', 'total', 'pct' of this week's top category
        top_cat_week_total – denominator used for pct above
        highest_exp – highest single expense this week (dict) or None
    """
    this_week  = db.get_weekly_total()
    last_week  = db.get_last_week_total()
    highest    = db.get_highest_weekly_expense()

    # Week-over-week change
    if last_week > 0:
        change_pct = ((this_week - last_week) / last_week) * 100
    elif this_week > 0:
        change_pct = 100.0
    else:
        change_pct = 0.0

    # Top category *this week*
    from datetime import datetime, timedelta
    from config import DATE_FORMAT
    today          = datetime.now()
    start_of_week  = today - timedelta(days=today.weekday())
    start_str      = start_of_week.strftime(DATE_FORMAT)
    end_str        = today.strftime(DATE_FORMAT)

    cursor = db.conn.cursor()
    cursor.execute(
        """SELECT category, COALESCE(SUM(amount), 0) as total
           FROM expenses WHERE date >= ? AND date <= ?
           GROUP BY category ORDER BY total DESC LIMIT 1""",
        (start_str, end_str),
    )
    row = cursor.fetchone()
    top_cat = None
    if row:
        pct = (row["total"] / this_week * 100) if this_week > 0 else 0
        top_cat = {
            "category": row["category"],
            "total":    row["total"],
            "pct":      pct,
        }

    return {
        "this_week":  this_week,
        "last_week":  last_week,
        "change_pct": change_pct,
        "top_cat":    top_cat,
        "highest_exp": highest,
    }


def get_warnings_alerts(db, budget):
    """
    Return a list of warning/alert dicts. Each item:
        { "level": "warning"|"alert", "icon": str, "message": str }
    """
    results = []
    this_week  = db.get_weekly_total()
    last_week  = db.get_last_week_total()
    breakdown  = db.get_category_breakdown()
    total      = db.get_total()

    # 1. Category exceeds 50% of all-time spending
    if breakdown and total > 0:
        top = breakdown[0]
        pct = (top["total"] / total) * 100
        if pct > 50:
            results.append({
                "level":   "warning",
                "icon":    "⚠️",
                "message": (
                    f"{top['category']} makes up {pct:.0f}% of your total spending. "
                    "Consider spreading expenses across other categories."
                ),
            })

    # 2. Weekly increase > 30%
    if last_week > 0:
        week_change = ((this_week - last_week) / last_week) * 100
        if week_change > 30:
            results.append({
                "level":   "alert",
                "icon":    "🚨",
                "message": (
                    f"Your spending jumped {week_change:.0f}% compared to last week "
                    f"({CURRENCY_SYMBOL}{this_week:,.0f} vs {CURRENCY_SYMBOL}{last_week:,.0f}). "
                    "Review large expenses."
                ),
            })

    # 3. Close to budget limit (≥ 80%)
    if budget > 0:
        monthly = db.get_monthly_total()
        pct_used = (monthly / budget) * 100
        if pct_used >= 100:
            results.append({
                "level":   "alert",
                "icon":    "🚨",
                "message": (
                    f"Budget exceeded! You've spent {CURRENCY_SYMBOL}{monthly:,.0f} "
                    f"against a {CURRENCY_SYMBOL}{budget:,.0f} budget this month."
                ),
            })
        elif pct_used >= 80:
            remaining = budget - monthly
            results.append({
                "level":   "warning",
                "icon":    "⚠️",
                "message": (
                    f"You've used {pct_used:.0f}% of your monthly budget. "
                    f"Only {CURRENCY_SYMBOL}{remaining:,.0f} remaining."
                ),
            })

    return results


def get_suggestions(db, budget):
    """
    Return a list of plain-English suggestion strings.
    """
    suggestions = []
    this_week   = db.get_weekly_total()
    last_week   = db.get_last_week_total()
    breakdown   = db.get_category_breakdown()
    total       = db.get_total()

    if total == 0:
        return ["Start tracking your expenses to get personalised suggestions."]

    # Heavy category suggestion
    if breakdown and total > 0:
        top = breakdown[0]
        pct = (top["total"] / total) * 100
        if pct > 40:
            suggestions.append(
                f"You are spending heavily on {top['category']} ({pct:.0f}% of total). "
                "Try reducing this category to stay within budget."
            )

    # Week-on-week increase
    if last_week > 0:
        week_change = ((this_week - last_week) / last_week) * 100
        if week_change > 20:
            suggestions.append(
                "Your spending increased this week. Review your large expenses and identify "
                "areas where you can cut back."
            )
        elif week_change < -20:
            suggestions.append(
                "Great job! Your spending dropped this week. Keep up the good habits."
            )

    # Budget-related suggestions
    if budget > 0:
        monthly = db.get_monthly_total()
        pct_used = (monthly / budget) * 100
        if pct_used >= 90:
            suggestions.append(
                "You're very close to your monthly budget limit. Avoid non-essential "
                "purchases for the rest of the month."
            )
        elif pct_used < 50:
            suggestions.append(
                f"You've used only {pct_used:.0f}% of your budget so far — you're on track!"
            )

    # Low diversity: only 1-2 categories
    if breakdown and len(breakdown) <= 2:
        suggestions.append(
            "You track expenses in very few categories. Adding more detail helps you "
            "spot patterns and reduce unnecessary spending."
        )

    # Fallback
    if not suggestions:
        suggestions.append(
            "Your spending looks balanced. Keep monitoring regularly to stay on top of your finances."
        )

    return suggestions


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