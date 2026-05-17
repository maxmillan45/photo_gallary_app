from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Photo, UserInteraction, Profile
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, CustomPasswordChangeForm

def register(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegisterForm()
    
    return render(request, 'gallery/register.html', {'form': form})


@login_required
def profile(request):
    """Display user profile"""
    user_photos = Photo.objects.filter(uploaded_by=request.user)
    return render(request, 'gallery/profile.html', {
        'user': request.user,
        'user_photos': user_photos
    })


@login_required
def edit_profile(request):
    """Edit user profile"""
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    
    return render(request, 'gallery/edit_profile.html', {
        'u_form': u_form,
        'p_form': p_form
    })


@login_required
def change_password(request):
    """Change user password"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'gallery/change_password.html', {'form': form})


def home(request):
    """Display homepage with all photos"""
    photos = Photo.objects.all().order_by('-created_at')
    tags = set()
    for photo in photos:
        tags.update(photo.get_tags_list())
    
    # Add user interaction status for logged in users
    if request.user.is_authenticated:
        for photo in photos:
            try:
                interaction = UserInteraction.objects.get(user=request.user, photo=photo)
                photo.user_interaction = interaction.interaction_type
            except UserInteraction.DoesNotExist:
                photo.user_interaction = None
    
    return render(request, 'gallery/home.html', {
        'photos': photos,
        'tags': sorted(list(tags))
    })


def photo_detail(request, photo_id):
    """Display photo details"""
    photo = get_object_or_404(Photo, id=photo_id)
    user_interaction = None
    
    if request.user.is_authenticated:
        try:
            interaction = UserInteraction.objects.get(user=request.user, photo=photo)
            user_interaction = interaction.interaction_type
        except UserInteraction.DoesNotExist:
            pass
    
    # Get all tags for filtering
    all_tags = set()
    all_photos = Photo.objects.all()
    for p in all_photos:
        all_tags.update(p.get_tags_list())
    
    return render(request, 'gallery/photo_detail.html', {
        'photo': photo,
        'user_interaction': user_interaction,
        'all_tags': sorted(list(all_tags))
    })


@login_required
def toggle_like(request, photo_id):
    """Handle like/dislike toggle for photos"""
    photo = get_object_or_404(Photo, id=photo_id)
    
    # Check if user already has interaction
    try:
        interaction = UserInteraction.objects.get(user=request.user, photo=photo)
        if interaction.interaction_type == 'like':
            # User already liked - remove like
            interaction.delete()
            liked = False
            message = 'Like removed'
        else:
            # User had disliked - change to like
            interaction.interaction_type = 'like'
            interaction.save()
            liked = True
            message = 'Photo liked!'
    except UserInteraction.DoesNotExist:
        # No interaction - create like
        UserInteraction.objects.create(user=request.user, photo=photo, interaction_type='like')
        liked = True
        message = 'Photo liked!'
    
    # Get updated counts
    likes_count = photo.likes_count
    dislikes_count = photo.dislikes_count
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'likes_count': likes_count,
            'dislikes_count': dislikes_count,
            'message': message
        })
    
    return redirect('photo_detail', photo_id=photo_id)


@login_required
def toggle_dislike(request, photo_id):
    """Handle dislike toggle for photos"""
    photo = get_object_or_404(Photo, id=photo_id)
    
    # Check if user already has interaction
    try:
        interaction = UserInteraction.objects.get(user=request.user, photo=photo)
        if interaction.interaction_type == 'dislike':
            # User already disliked - remove dislike
            interaction.delete()
            disliked = False
            message = 'Dislike removed'
        else:
            # User had liked - change to dislike
            interaction.interaction_type = 'dislike'
            interaction.save()
            disliked = True
            message = 'Photo disliked!'
    except UserInteraction.DoesNotExist:
        # No interaction - create dislike
        UserInteraction.objects.create(user=request.user, photo=photo, interaction_type='dislike')
        disliked = True
        message = 'Photo disliked!'
    
    # Get updated counts
    likes_count = photo.likes_count
    dislikes_count = photo.dislikes_count
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'disliked': disliked,
            'likes_count': likes_count,
            'dislikes_count': dislikes_count,
            'message': message
        })
    
    return redirect('photo_detail', photo_id=photo_id)


def filter_by_tag(request, tag):
    """Filter photos by tag"""
    photos = []
    all_photos = Photo.objects.all().order_by('-created_at')
    
    for photo in all_photos:
        if tag.lower() in [t.lower() for t in photo.get_tags_list()]:
            photos.append(photo)
    
    # Get all unique tags
    all_tags = set()
    for photo in Photo.objects.all():
        all_tags.update(photo.get_tags_list())
    
    # Add user interaction status for logged in users
    if request.user.is_authenticated:
        for photo in photos:
            try:
                interaction = UserInteraction.objects.get(user=request.user, photo=photo)
                photo.user_interaction = interaction.interaction_type
            except UserInteraction.DoesNotExist:
                photo.user_interaction = None
    
    return render(request, 'gallery/home.html', {
        'photos': photos,
        'tags': sorted(list(all_tags)),
        'current_tag': tag
    })