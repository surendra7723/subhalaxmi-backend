from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, TemplateView, DetailView
from django.contrib import messages
from django.db.models import Prefetch, Count, Avg
from store.models import Product, ProductImage, ProductVideo
from store.forms import ContactForm


class HomeView(TemplateView):
    template_name = 'store/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Use the optimized manager method for featured products
        context['featured_products'] = Product.objects.featured().order_by('-created_at')[:6]
        
        # Add additional product collections with minimal queries
        context['new_arrivals'] = Product.objects.new_arrivals().order_by('-created_at')[:4]
        context['best_sellers'] = Product.objects.best_sellers().order_by('-review_count')[:4]
        context['on_sale'] = Product.objects.on_sale().order_by('-discount')[:4]
        
        # Add context for statistics (single queries, no JOINs)
        context['total_products'] = Product.objects.count()
        context['featured_count'] = Product.objects.filter(is_featured=True).count()
        context['new_arrivals_count'] = Product.objects.filter(is_new=True).count()
        
        return context


class ProductListView(ListView):
    model = Product
    template_name = 'store/product_list.html'
    context_object_name = 'products'
    paginate_by = 12  # Add pagination for better performance

    def get_queryset(self):
        # Start with optimized queryset
        queryset = Product.objects.with_media()
        
        # Handle category filtering
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
            
        # Handle other filters
        brand = self.request.GET.get('brand')
        if brand:
            queryset = queryset.filter(brand=brand)
            
        gender = self.request.GET.get('gender')
        if gender:
            queryset = queryset.filter(gender=gender)
            
        # Handle price range filtering
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
            
        # Handle special filters
        is_featured = self.request.GET.get('featured')
        if is_featured:
            queryset = queryset.filter(is_featured=True)
            
        is_new = self.request.GET.get('new')
        if is_new:
            queryset = queryset.filter(is_new=True)
            
        is_on_sale = self.request.GET.get('sale')
        if is_on_sale:
            queryset = queryset.filter(is_on_sale=True)
            
        # Handle sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        allowed_sorts = [
            'name', '-name', 'price', '-price', 'created_at', '-created_at',
            'average_rating', '-average_rating', 'review_count', '-review_count'
        ]
        if sort_by in allowed_sorts:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('-created_at')
            
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter context for the template
        context['current_category'] = self.request.GET.get('category', '')
        context['current_brand'] = self.request.GET.get('brand', '')
        context['current_gender'] = self.request.GET.get('gender', '')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        
        # Get unique categories and brands for filter options
        context['categories'] = Product.objects.values_list('category', flat=True).distinct()
        context['brands'] = Product.objects.values_list('brand', flat=True).distinct()
        context['genders'] = Product.objects.values_list('gender', flat=True).distinct()
        
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'store/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        # Use optimized queryset with media
        return Product.objects.with_media()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get related products from the same category (optimized)
        if self.object.category:
            context['related_products'] = Product.objects.with_media().filter(
                category=self.object.category
            ).exclude(
                id=self.object.id
            )[:4]
        
        # Get primary image and video for quick access
        context['primary_image'] = self.object.get_primary_image()
        
        # Use optimized attributes from manager
        optimized_images = getattr(self.object, 'optimized_images', None)
        optimized_videos = getattr(self.object, 'optimized_videos', None)
        
        if optimized_images is not None:
            context['has_multiple_images'] = len(optimized_images) > 1
        else:
            context['has_multiple_images'] = self.object.images.count() > 1
            
        if optimized_videos is not None:
            context['has_videos'] = len(optimized_videos) > 0
        else:
            context['has_videos'] = self.object.videos.count() > 0
        
        return context


class AboutView(TemplateView):
    template_name = 'store/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add some statistics for the about page if needed
        context['total_products'] = Product.objects.count()
        context['total_categories'] = Product.objects.values('category').distinct().count()
        context['featured_products_count'] = Product.objects.filter(is_featured=True).count()
        
        return context


class ContactView(TemplateView):
    template_name = 'store/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ContactForm()
        return context
    
    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save()
            messages.success(
                request, 
                f"Thank you, {contact_message.first_name}! Your message has been sent successfully. "
                "We'll get back to you within 24 hours."
            )
            return redirect('store:contact')
        else:
            messages.error(
                request,
                "There was an error with your submission. Please check the form and try again."
            )
            return render(request, self.template_name, {'form': form})  