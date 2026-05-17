from django.contrib import admin
from .models import Profile, Photo, UserInteraction

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'location', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone']

@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ['title', 'uploaded_by', 'created_at', 'likes_count', 'dislikes_count']
    list_filter = ['created_at', 'tags']
    search_fields = ['title', 'description', 'tags', 'uploaded_by__username']

@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'photo', 'interaction_type', 'created_at']
    list_filter = ['interaction_type', 'created_at']