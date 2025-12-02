from django.shortcuts import render, redirect, get_object_or_404
from .static.foodSearch import get_food_data, get_food_by_fdcId
from .static.nutrient_functions import get_dv_avg, get_log_items
from django.core.paginator import Paginator
from django.core.cache import cache
from datetime import date, timedelta
from .models import Profile, LogItem
from .forms import SignUpForm, PercentConsumedForm, DateConsumedForm, LogItemForm
from collections import OrderedDict
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as auth_logout


def search(request):
    query = request.GET.get("q")
    foods = []

    if query:
        cache_key = f"food_results_{query.lower()}"
        foods = cache.get(cache_key)

        if not foods:
            foods = get_food_data(query)
            if foods is None:  # Ensure it's not None
                foods = []  # Set to an empty list if None
            cache.set(cache_key, foods, timeout=60 * 60)  # Cache for 1 hour

    paginator = Paginator(foods, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, 'search.html',
                  {"page_obj": page_obj, "query": query})

@login_required
def index(request):
    """View function for home page of site."""
    cur_profile = request.user.profile
    profile_Id = cur_profile.id
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
    cur_profile = request.user.profile
    profile_Id = cur_profile.id
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


@login_required
def save_logItem(request, fdcId):
    """Endpoint for saving logItem"""
    foodItem = get_food_by_fdcId(fdcId)
    
    cur_profile = request.user.profile
    profile_Id = cur_profile.id
    profile = Profile.objects.get(id=profile_Id)
    if request.method == 'POST':
        form = LogItemForm(request.POST)
        if form.is_valid():
            LogItem.objects.create(
                profile=profile,
                date=form.cleaned_data['date'],
                percentConsumed=form.cleaned_data['percentConsumed'],
                foodItem=foodItem
            )
            return HttpResponseRedirect(reverse('index'))
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


@login_required
def profile(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = None
    return render(request, 'profile.html', {'profile': profile})


@login_required
def edit_profile(request):
    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        profile = Profile(user=request.user)

    from .forms import ProfileForm

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return HttpResponseRedirect(reverse('profile'))
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'profile_edit.html', {'form': form})


def logout_view(request):
    """Log the user out and render a custom logged out page."""
    auth_logout(request)
    messages.info(request, "You've been logged out.")
    return render(request, 'logged_out.html')



def signup(request):
    User = get_user_model()
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            birthdate = form.cleaned_data.get('birthdate')
            height = form.cleaned_data.get('height')
            weight = form.cleaned_data.get('weight')
            now = date.today()
            age = now.year - birthdate.year - ((now.month, now.day) < (birthdate.month, birthdate.day))
            

            # check for existing username/email
            if User.objects.filter(username=username).exists():
                form.add_error('username', 'Username already taken.')
            elif User.objects.filter(email=email).exists():
                form.add_error('email', 'Email already registered.')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                Profile.objects.create(user=user, age=age, birthdate=birthdate, height=height, weight=weight)
                # Log the user in and show a success message
                auth_login(request, user)
                messages.success(request, 'Account created and you are now logged in.')
                return HttpResponseRedirect(reverse('index'))
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})
