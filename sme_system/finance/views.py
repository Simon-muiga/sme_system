from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum
from django.http import HttpResponse
from reportlab.pdfgen import canvas
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.db.models.functions import TruncMonth

from .models import BusinessProfile, Sale, Expense, Prediction
from .forms import ExpenseForm, SaleForm, RegisterForm
from .models import Category
from .forms import CategoryForm

import random

from datetime import datetime
import calendar

# =========================
# REGISTER
# =========================
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registration successful. Please log in.")
            return redirect("login")
    else:
        form = RegisterForm()

    return render(request, "finance/register.html", {"form": form})


# =========================
# DASHBOARD
# =========================
@login_required
def dashboard(request):

    try:
        business = request.user.businessprofile
    except BusinessProfile.DoesNotExist:
        return redirect("create_business_profile")

    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    sales = Sale.objects.filter(business=business)
    expenses = Expense.objects.filter(business=business)

    if start_date:
        sales = sales.filter(date__gte=start_date)
        expenses = expenses.filter(date__gte=start_date)

    if end_date:
        sales = sales.filter(date__lte=end_date)
        expenses = expenses.filter(date__lte=end_date)

    # ===== SUMMARY =====
    total_sales = sales.aggregate(Sum("amount"))["amount__sum"] or 0
    total_expenses = expenses.aggregate(Sum("amount"))["amount__sum"] or 0

    summary_raw = {
        "total_sales": total_sales,
        "total_expenses": total_expenses,
        "net_profit": total_sales - total_expenses,
    }

    # ===== PROFIT MARGIN =====
    profit_margin = 0

    if total_sales > 0:
        profit_margin = (summary_raw["net_profit"] / total_sales) * 100

    summary = {key.replace("_", " ").title(): value for key, value in summary_raw.items()}

    # ===== MONTHLY REPORT =====
    monthly_sales = (
        Sale.objects.filter(business=business)
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total_sales=Sum("amount"))
    )

    monthly_expenses = (
        Expense.objects.filter(business=business)
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total_expenses=Sum("amount"))
    )

    report = {}

    for item in monthly_sales:
        report[item["month"]] = {
            "sales": item["total_sales"],
            "expenses": 0
        }

    for item in monthly_expenses:
        if item["month"] not in report:
            report[item["month"]] = {"sales": 0, "expenses": 0}

        report[item["month"]]["expenses"] = item["total_expenses"]

    monthly_report = []

    for month, data in report.items():
        monthly_report.append({
            "month": month.strftime("%B %Y"),
            "sales": data["sales"],
            "expenses": data["expenses"],
            "profit": data["sales"] - data["expenses"]
        })

    profit_labels = []
    profit_sales = []
    profit_expenses = []

    for item in monthly_report:
        profit_labels.append(item["month"])
        profit_sales.append(float(item["sales"]))
        profit_expenses.append(float(item["expenses"]))

   

    # ===== Latest Records =====
    sales_latest = sales.order_by("-date")[:5]
    expenses_latest = expenses.order_by("-date")[:5]

    # ===== EXPENSE PIE CHART =====
    expenses_by_category = (
        Expense.objects.filter(business=business)
        .values("category__name")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    )

    expense_labels = [item["category__name"] or "No Category" for item in expenses_by_category]
    expense_data = [float(item["total"]) for item in expenses_by_category]

    # Generate random colors dynamically
    def random_color():
        return "#" + ''.join([random.choice("0123456789ABCDEF") for _ in range(6)])
    
    expense_colors = [random_color() for _ in expense_labels]

    # ==== TOP EXPENSE CATEGORY =====
    top_category = None
    top_amount = 0

    if expense_labels and expense_data:
        top_index = expense_data.index(max(expense_data))
        top_category = expense_labels[top_index]
        top_amount = expense_data[top_index]

    # ===== SALES LINE CHART =====
    sales_by_date = sales.values("date").annotate(total=Sum("amount")).order_by("date")

    sales_labels = [str(item["date"]) for item in sales_by_date]
    sales_data = [float(item["total"]) for item in sales_by_date]

    # ===== SIMPLE SALES PREDICTION =====

    monthly_sales_prediction = (
        Sale.objects.filter(business=business)
        .annotate(month=TruncMonth("date"))
        .values("month")
        .annotate(total_sales=Sum("amount"))
        .order_by("month")
    )

    prediction_labels = []
    prediction_data = []

    sales_values = [float(item["total_sales"]) for item in monthly_sales_prediction]

    if sales_values:
        avg_sales = sum(sales_values) / len(sales_values)

        today = datetime.today()
        next_month = today.month + 1
        year = today.year

        if next_month > 12:
            next_month = 1
            year += 1

            month_name = calendar.month_name[next_month]

            prediction_labels.append(month_name)
            prediction_data.append(round(avg_sales, 2))
    return render(
        request,
        "finance/dashboard.html",
        {
            "summary": summary,
            "sales": sales_latest,
            "expenses": expenses_latest,
            "monthly_report": monthly_report,
            "start_date": start_date or "",
            "end_date": end_date or "",
            "expense_labels": json.dumps(expense_labels),
            "expense_data": json.dumps(expense_data),
            "expense_colors": json.dumps(expense_colors),
            "sales_labels": json.dumps(sales_labels),
            "sales_data": json.dumps(sales_data),
            "profit_labels": json.dumps(profit_labels),
            "profit_sales": json.dumps(profit_sales),
            "profit_expenses": json.dumps(profit_expenses),
            "top_category": top_category,
            "top_amount": top_amount,
            "profit_margin": profit_margin,
            "prediction_labels" : json.dumps(prediction_labels),
            "prediction_data" : json.dumps(prediction_data)

        },
    )


# =========================
# ADD EXPENSE
# =========================
@login_required
def add_expense(request):

    try:
        business = request.user.businessprofile
    except BusinessProfile.DoesNotExist:
        return redirect("create_business_profile")

    if request.method == "POST":
        form = ExpenseForm(request.POST)

        if form.is_valid():
            expense = form.save(commit=False)
            expense.business = business
            expense.save()
            return redirect("dashboard")

    else:
        form = ExpenseForm()

    return render(request, "finance/add_expense.html", {"form": form})


# =========================
# ADD SALE
# =========================
@login_required
def add_sale(request):

    try:
        business = request.user.businessprofile
    except BusinessProfile.DoesNotExist:
        return redirect("create_business_profile")

    if request.method == "POST":
        form = SaleForm(request.POST)

        if form.is_valid():
            sale = form.save(commit=False)
            sale.business = business
            sale.save()
            return redirect("dashboard")

    else:
        form = SaleForm()

    return render(request, "finance/add_sale.html", {"form": form})


# =========================
# EDIT SALE
# =========================
@login_required
def edit_sale(request, pk):

    try:
        business = request.user.businessprofile
    except BusinessProfile.DoesNotExist:
        return redirect("create_business_profile")

    sale = get_object_or_404(Sale, pk=pk, business=business)

    if request.method == "POST":
        form = SaleForm(request.POST, instance=sale)

        if form.is_valid():
            form.save()
            return redirect("dashboard")

    else:
        form = SaleForm(instance=sale)

    return render(request, "finance/add_sale.html", {"form": form})


# =========================
# DELETE SALE
# =========================
@login_required
def delete_sale(request, pk):

    try:
        business = request.user.businessprofile
    except BusinessProfile.DoesNotExist:
        return redirect("create_business_profile")

    sale = get_object_or_404(Sale, pk=pk, business=business)
    sale.delete()

    return redirect("dashboard")


# =========================
# EDIT EXPENSE
# =========================
@login_required
def edit_expense(request, pk):

    try:
        business = request.user.businessprofile
    except BusinessProfile.DoesNotExist:
        return redirect("create_business_profile")

    expense = get_object_or_404(Expense, pk=pk, business=business)

    if request.method == "POST":
        form = ExpenseForm(request.POST, instance=expense)

        if form.is_valid():
            form.save()
            return redirect("dashboard")

    else:
        form = ExpenseForm(instance=expense)

    return render(request, "finance/add_expense.html", {"form": form})


# =========================
# DELETE EXPENSE
# =========================
@login_required
def delete_expense(request, pk):

    try:
        business = request.user.businessprofile
    except BusinessProfile.DoesNotExist:
        return redirect("create_business_profile")

    expense = get_object_or_404(Expense, pk=pk, business=business)
    expense.delete()

    return redirect("dashboard")


# =========================
# CREATE BUSINESS PROFILE
# =========================
@login_required
def create_business_profile(request):

    try:
        if request.user.businessprofile:
            return redirect("dashboard")
    except BusinessProfile.DoesNotExist:
        pass

    if request.method == "POST":

        business_name = request.POST.get("business_name")
        industry = request.POST.get("industry")

        if business_name and industry:
            BusinessProfile.objects.create(
                user=request.user,
                business_name=business_name,
                industry=industry
            )

            return redirect("dashboard")

    return render(request, "finance/create_business_profile.html")

@login_required
def download_report(request):

    business = request.user.businessprofile

    sales_total = Sale.objects.filter(business=business).aggregate(Sum("amount"))["amount__sum"] or 0
    expenses_total = Expense.objects.filter(business=business).aggregate(Sum("amount"))["amount__sum"] or 0
    profit = sales_total - expenses_total

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="financial_report.pdf"'

    p = canvas.Canvas(response)

    p.setFont("Helvetica", 16)
    p.drawString(200, 800, "Financial Report")

    p.setFont("Helvetica", 12)
    p.drawString(100, 750, f"Total Sales: Ksh {sales_total:.2f}")
    p.drawString(100, 730, f"Total Expenses: Ksh {expenses_total:.2f}")
    p.drawString(100, 710, f"Net Profit: Ksh {profit:.2f}")

    p.showPage()
    p.save()

    return response

@login_required
def categories(request):

    business = request.user.businessprofile

    categories = Category.objects.filter(business=business)

    context = {
        "categories": categories
    }

    return render(request, "finance/categories.html", context)

@login_required
def add_category(request):

    business = request.user.businessprofile

    if request.method == "POST":

        form = CategoryForm(request.POST)

        if form.is_valid():

            category = form.save(commit=False)
            category.business = business
            category.save()

            return redirect("categories")
        
    else:
        form = CategoryForm()
        
    context = {
            "form": form
        }
   
    return render(request, "finance/add_category.html", context)

@login_required
def edit_category(request, pk):

    business = request.user.businessprofile

    category = get_object_or_404(
        Category,
        pk=pk,
        business=business
    )

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)

        if form.is_valid():
            form.save()
            return redirect("categories")
    else:
        form = CategoryForm(instance=category)

    context = {
        "form": form,
        "category": category,
    }

    return render(request, "finance/add_category.html", context)

@login_required
def delete_category(request, pk):

    business = request.user.businessprofile 

    category = get_object_or_404(
        Category,
        pk=pk,
        business=business
    )

    category.delete()

    return redirect("categories")


