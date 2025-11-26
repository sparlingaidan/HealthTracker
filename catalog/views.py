from django.shortcuts import render, redirect, get_object_or_404
from .static.foodSearch import get_food_data, get_food_by_fdcId
from .static.nutrient_functions import get_dv_avg, get_log_items
from django.core.paginator import Paginator
from django.core.cache import cache
from datetime import datetime, timedelta
from .models import Profile, LogItem
from .forms import PercentConsumedForm, DateConsumedForm, LogItemForm
from collections import OrderedDict
from django.utils import timezone


def search(request):
    query = request.GET.get("q")
    foods = []

    if query:
        cache_key = f"food_results_{query.lower()}"
        foods = cache.get(cache_key)

        if not foods:
            foods = get_food_data(query)
            cache.set(cache_key, foods, timeout=60 * 60)  # Cache for 1 hour

    paginator = Paginator(foods, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, 'search.html',
                  {"page_obj": page_obj, "query": query})


def index(request):
    """View function for home page of site."""
    profile_Id = 1  # Change when we can Login.
    end = timezone.now()
    start = end - timedelta(days=7)

    '''start date, end date, #profile_id'''
    averages = get_dv_avg(start, end, profile_Id)

    '''Sort gauges by nutrinet_funtions.deviaiton, Worst first '''
    nutrients = sorted(
        averages.items(),
        key=lambda item: int(item[1]['deviation']),
        reverse=True)
    nutrients = OrderedDict(nutrients)

    context = {
        'nutrients': nutrients
    }

    return render(request, 'index.html', context=context)


def edit(request):
    """View function for home page of site."""
    profile_Id = 1  # Change when we can Login.
    now = timezone.now()
    start = now - \
        timedelta(days=730)
    end = now + \
        timedelta(days=730)

    LogItems = get_log_items(start, end, profile_Id)

    context = {
        'LogItems': LogItems
    }

    return render(request, 'edit.html', context)


def update_percent(request, log_id):
    """Endpiont for updating_percent"""
    log_item = get_object_or_404(LogItem, id=log_id)

    if request.method == 'POST':
        form = PercentConsumedForm(request.POST, instance=log_item)
        if form.is_valid():
            form.save()
            return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            return render(request, '404.html', None)


def update_date(request, log_id):
    """Endpiont for updating_date"""
    log_item = get_object_or_404(LogItem, id=log_id)

    if request.method == 'POST':
        form = DateConsumedForm(request.POST, instance=log_item)
        if form.is_valid():
            form.save()
            return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            return render(request, '404.html', None)


def save_logItem(request, fdcId):
    """Endpoint for saving logItem"""
    foodItem = get_food_by_fdcId(fdcId)
    profile = Profile.objects.get(id=1)
    if request.method == 'POST':
        form = LogItemForm(request.POST)
        if form.is_valid():
            LogItem.objects.create(
                profile=profile,
                date=form.cleaned_data['date'],
                percentConsumed=form.cleaned_data['percentConsumed'],
                foodItem=foodItem
            )
            return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            return render(request, '404.html', None)


def delete_logItem(request):
    """Endpoint for deleting logItem,  When we can login
    I think we need to authenticate the user somehow?"""
    if request.method == 'POST':
        log_id =(request.POST['logItem_id'])
        log_item = get_object_or_404(LogItem, id=log_id)
        log_item.delete()
        if log_id:
            return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            return render(request, '404.html', None)