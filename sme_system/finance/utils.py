from .models import Sale, Expense

def calculate_financial_summary(business):
    """
    Calculates total sales, total expenses, and net profit
    for a given business.
    """
    # Get all sales and expenses for this business
    sales = Sale.objects.filter(business=business)
    expenses = Expense.objects.filter(business=business)

    # Sum up amounts
    total_sales = sum(s.amount for s in sales)
    total_expenses = sum(e.amount for e in expenses)

    # Calculate net profit
    net_profit = total_sales - total_expenses

    return {
        "total_sales": total_sales,
        "total_expenses": total_expenses,
        "net_profit": net_profit
    }
