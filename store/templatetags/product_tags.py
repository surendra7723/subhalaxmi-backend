from django import template
from django.db.models import Count

register = template.Library()

@register.inclusion_tag('store/includes/product_card.html')
def product_card(product, show_category=True, show_brand=False):
    """
    Optimized product card template tag that uses prefetched data
    """
    # Use optimized images if available, fallback to regular queryset
    images = getattr(product, 'optimized_images', None)
    if images is None:
        images = product.images.all()
    
    # Use optimized videos if available, fallback to regular queryset
    videos = getattr(product, 'optimized_videos', None)
    if videos is None:
        videos = product.videos.all()
    
    # Get primary image efficiently
    primary_image = product.get_primary_image()
    if not primary_image and images:
        primary_image = images[0] if hasattr(images, '__getitem__') else images.first()
    
    # Get first video efficiently
    first_video = videos[0] if hasattr(videos, '__getitem__') and videos else (videos.first() if videos else None)
    
    return {
        'product': product,
        'primary_image': primary_image,
        'first_video': first_video,
        'has_video': bool(first_video),
        'show_category': show_category,
        'show_brand': show_brand,
    }

@register.filter
def get_optimized_images(product):
    """
    Template filter to get optimized images or fallback to regular images
    """
    optimized = getattr(product, 'optimized_images', None)
    if optimized is not None:
        return optimized
    return product.images.all()

@register.filter
def get_optimized_videos(product):
    """
    Template filter to get optimized videos or fallback to regular videos
    """
    optimized = getattr(product, 'optimized_videos', None)
    if optimized is not None:
        return optimized
    return product.videos.all()

@register.filter
def has_multiple_media(product):
    """
    Check if product has multiple images or any videos
    """
    image_count = getattr(product, 'image_count', None)
    video_count = getattr(product, 'video_count', None)
    
    if image_count is not None and video_count is not None:
        return (image_count + video_count) > 1
    
    # Fallback to database queries if counts not available
    return (product.images.count() + product.videos.count()) > 1

@register.simple_tag
def get_product_stats():
    """
    Get product statistics for display
    """
    from store.models import Product
    
    return {
        'total': Product.objects.count(),
        'featured': Product.objects.filter(is_featured=True).count(),
        'new': Product.objects.filter(is_new=True).count(),
        'on_sale': Product.objects.filter(is_on_sale=True).count(),
    }

@register.simple_tag
def get_filter_options():
    """
    Get filter options for product listing
    """
    from store.models import Product
    
    return {
        'categories': Product.objects.values_list('category', flat=True).distinct().order_by('category'),
        'brands': Product.objects.values_list('brand', flat=True).distinct().order_by('brand'),
        'genders': Product.objects.values_list('gender', flat=True).distinct().order_by('gender'),
    }
