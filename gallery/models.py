from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
import os

class Profile(models.Model):
    """
    User profile model extending Django's built-in User model
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True, default='')
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, default='')
    location = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username}\'s Profile'

    def save(self, *args, **kwargs):
        """Override save to resize profile pictures"""
        super().save(*args, **kwargs)
        
        if self.profile_picture and os.path.exists(self.profile_picture.path):
            try:
                img = Image.open(self.profile_picture.path)
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)
                    img.save(self.profile_picture.path)
            except Exception as e:
                print(f"Error processing image: {e}")

# Signal to auto-create profile when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Automatically create profile when user is created"""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save profile when user is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()


class Photo(models.Model):
    """
    Photo model for storing gallery images
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='gallery_photos/')
    tags = models.CharField(max_length=500, help_text='Comma-separated tags (e.g., nature, city, portrait)')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photos')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_tags_list(self):
        """Return tags as a list"""
        return [tag.strip().lower() for tag in self.tags.split(',') if tag.strip()]

    @property
    def likes_count(self):
        """Get total number of likes"""
        return self.likes.count()

    @property
    def dislikes_count(self):
        """Get total number of dislikes"""
        return self.dislikes.count()

    @property
    def user_interaction(self):
        """Get user interaction for current user - will be used in views"""
        return None  # This will be set in the view context


class UserInteraction(models.Model):
    """
    Model to track user likes/dislikes on photos
    """
    INTERACTION_CHOICES = [
        ('like', 'Like'),
        ('dislike', 'Dislike'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactions')
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='interactions')
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'photo']  # One interaction per user per photo

    def __str__(self):
        return f"{self.user.username} - {self.interaction_type} - {self.photo.title}"