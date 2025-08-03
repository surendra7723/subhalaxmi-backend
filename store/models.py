from django.db import models
from django.db.models import Prefetch, Count

from store.constants import CATEGORY_CHOICES

# Create your models here.
class ProductManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_archived=False)
    
    def with_media(self):
        """Optimized queryset with prefetched images and videos"""
        from store.models import ProductImage, ProductVideo
        return self.get_queryset().prefetch_related(
            Prefetch(
                'images',
                queryset=ProductImage.objects.order_by('-is_primary', 'id'),
                to_attr='optimized_images'
            ),
            Prefetch(
                'videos',
                queryset=ProductVideo.objects.order_by('-is_primary', 'id'),
                to_attr='optimized_videos'
            )
        ).annotate(
            image_count=Count('images'),
            video_count=Count('videos')
        )
    
    def featured(self):
        """Get featured products with optimized media queries"""
        return self.with_media().filter(is_featured=True)
    
    def new_arrivals(self):
        """Get new arrival products with optimized media queries"""
        return self.with_media().filter(is_new=True)
    
    def on_sale(self):
        """Get products on sale with optimized media queries"""
        return self.with_media().filter(is_on_sale=True)
    
    def best_sellers(self):
        """Get best selling products with optimized media queries"""
        return self.with_media().filter(is_best_seller=True)

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    available_sizes = models.JSONField(default=list)
    available_colors = models.JSONField(default=list)
    category= models.CharField(max_length=100, choices = CATEGORY_CHOICES)
    brand = models.CharField(max_length=100)
    material = models.CharField(max_length=100)
    gender = models.CharField(max_length=50, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('unisex', 'Unisex'),
    ])
    season = models.CharField(max_length=50)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    sku = models.CharField(max_length=100, unique=True)
    average_rating = models.FloatField(default=0.0)
    review_count = models.IntegerField(default=0)
    tags = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_featured = models.BooleanField(default=False, verbose_name="Featured")
    is_new = models.BooleanField(default=False, verbose_name="New")
    is_on_sale = models.BooleanField(default=False, verbose_name="On Sale")
    is_best_seller = models.BooleanField(default=False, verbose_name="Best Seller")
    care_instructions = models.TextField(blank=True, null=True)
    return_policy = models.TextField(blank=True, null=True)
    shipping_info = models.TextField(blank=True, null=True)
    is_archived = models.BooleanField(default=False)

    objects = ProductManager()  # Custom manager for non-archived products
    all_objects = models.Manager()  # Default manager to include all products

    def delete(self, *args, **kwargs):
        """Soft delete the product by marking it as archived."""
        self.is_archived = True
        self.save()

    def get_primary_image(self):
        """Get the primary image or the first available image for this product."""
        primary_image = self.images.filter(is_primary=True).first()
        if primary_image:
            return primary_image
        return self.images.first()

    def __str__(self):
        return self.name
        
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(
        upload_to='product_images/',
        help_text='Supported formats: JPEG, PNG, WebP, GIF'
    )
    is_primary = models.BooleanField(default=False)
    alt_text = models.CharField(max_length=255, blank=True, help_text='Alternative text for accessibility')

    def clean(self):
        """Validate image format and size"""
        from django.core.exceptions import ValidationError
        
        if self.image:
            # Check file size (max 5MB)
            if self.image.size > 5 * 1024 * 1024:
                raise ValidationError("Image file too large. Maximum size is 5MB.")
            
            # Check file format
            allowed_formats = ['JPEG', 'PNG', 'WEBP', 'GIF']
            try:
                from PIL import Image
                img = Image.open(self.image)
                if img.format not in allowed_formats:
                    raise ValidationError(f"Unsupported image format. Allowed: {', '.join(allowed_formats)}")
            except Exception:
                raise ValidationError("Invalid image file.")

    def __str__(self):
        return f"{self.product.name} - Image"
    
    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['-is_primary', 'id']
        
        
class ProductVideo(models.Model):
    product = models.ForeignKey(Product, related_name='videos', on_delete=models.CASCADE)
    video = models.FileField(upload_to='product_videos/')
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.product.name} - Video"

    class Meta:
        verbose_name = 'Product Video'
        verbose_name_plural = 'Product Videos'
        ordering = ['id']


class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ('product_inquiry', 'Product Inquiry'),
        ('order_status', 'Order Status'),
        ('sizing_help', 'Sizing Help'),
        ('styling_advice', 'Styling Advice'),
        ('return_exchange', 'Return/Exchange'),
        ('complaint', 'Complaint'),
        ('compliment', 'Compliment'),
        ('wholesale', 'Wholesale Inquiry'),
        ('other', 'Other'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    subject = models.CharField(max_length=20, choices=SUBJECT_CHOICES)
    message = models.TextField()
    newsletter_signup = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)
    admin_notes = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.get_subject_display()}"
    
    class Meta:
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        ordering = ['-created_at']