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
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm 

@login_required
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
    yesterday = end - timedelta(days=1)

    '''start date, end date, #profile_id'''
    averages = get_dv_avg(start, end, profile_Id)

    '''Sort gauges by nutrinet_funtions.deviaiton, Worst first '''
    nutrients = sorted(
        averages.items(),
        key=lambda item: int(item[1]['deviation']),
        reverse=True)
    nutrients = OrderedDict(nutrients)


    '''start date, end date, #profile_id'''
    daily_averages = get_dv_avg(yesterday, end, profile_Id)

    '''Sort gauges by nutrinet_funtions.deviaiton, Worst first '''
    daily_nutrients = sorted(
        daily_averages.items(),
        key=lambda item: int(item[1]['deviation']),
        reverse=True)
    daily_nutrients = OrderedDict(daily_nutrients)

    context = {
        'daily_nutrients': daily_nutrients,
        'nutrients': nutrients,
    }

    return render(request, 'index.html', context=context)

@login_required
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

@login_required
def update_percent(request, log_id):
    """Endpiont for updating_percent"""
    log_item = get_object_or_404(LogItem, id=log_id)
    # Security check: Ensure the log item belongs to the authenticated user's profile
    if log_item.profile != request.user.profile:
        return redirect('index')

    if request.method == 'POST':
        form = PercentConsumedForm(request.POST, instance=log_item)
        if form.is_valid():
            form.save()
            return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            messages.error(request, "Failed to update consumption percentage.")
            return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def update_date(request, log_id):
    """Endpiont for updating_date"""
    log_item = get_object_or_404(LogItem, id=log_id)
    # Security check: Ensure the log item belongs to the authenticated user's profile
    if log_item.profile != request.user.profile:
        return redirect('index')

    if request.method == 'POST':
        form = DateConsumedForm(request.POST, instance=log_item)
        if form.is_valid():
            form.save()
            return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            messages.error(request, "Failed to update date.")
            return redirect(request.META.get('HTTP_REFERER', '/'))


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
            messages.error(request, "Could not save log item due to invalid form data.")
            # Redirect to the page where the form was submitted, if possible
            return redirect(request.META.get('HTTP_REFERER', reverse('search')))

@login_required
def delete_logItem(request):
    """Endpoint for deleting logItem, requires authentication."""
    if request.method == 'POST':
        log_id = request.POST.get('logItem_id')
        if not log_id:
            messages.error(request, "Invalid log item ID.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        log_item = get_object_or_404(LogItem, id=log_id)

        # Security check: Ensure the log item belongs to the authenticated user's profile
        if log_item.profile != request.user.profile:
            messages.error(request, "You do not have permission to delete this item.")
            return redirect(request.META.get('HTTP_REFERER', '/'))

        log_item.delete()
        messages.success(request, "Log item deleted successfully.")
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    # If not a POST request, redirect back
    return redirect(request.META.get('HTTP_REFERER', '/'))


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
        # If form is NOT valid, it falls through to render below, showing errors.
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})



def user_login(request):
    """
    Handles user login using Django's built-in AuthenticationForm
    to correctly handle form rendering, validation, and error messages
    expected by your login.html template.
    """
    # If the user is already authenticated, redirect them away from the login page
    if request.user.is_authenticated:
        return redirect(reverse('index'))

    if request.method == 'POST':
        # AuthenticationForm handles the request data (POST) and error messaging
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)

            # Redirect logic: look for 'next' parameter first, then default to 'index'
            next_url = request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect(reverse('index'))
        else:
            # If the form is not valid (bad credentials), add an error message
            messages.error(request, "Invalid username or password.")
            # Form rendering will automatically include validation errors in the template

    else:
        # GET request: Display an empty form
        form = AuthenticationForm()

    # Pass the form and 'next' parameter (from GET) to the template
    context = {
        'form': form,
        'next': request.GET.get('next', ''),
    }
    return render(request, 'login.html', context) # Assuming your template is named 'login.html' or 'registration/login.html'
