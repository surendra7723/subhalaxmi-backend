from django.contrib import admin
from .models import Product, ProductImage, ProductVideo, ContactMessage
from .forms import ProductAdminForm

# Register your models here.
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    min_num = 0
    max_num = 10
    can_delete = True
    fields = ('image', 'is_primary', 'alt_text')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-width: 100px; max-height: 100px;" />'
        return "No image"
    image_preview.short_description = 'Preview'
    image_preview.allow_tags = True


class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 0
    min_num = 0
    max_num = 5
    can_delete = True
    fields = ('video', 'is_primary')


    
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'category', 'is_featured', 'is_new', 'is_on_sale', 'is_best_seller')
    search_fields = ('name', 'category', 'brand', 'sku')
    list_filter = ('category', 'brand', 'gender', 'is_featured', 'is_new', 'is_on_sale', 'is_best_seller', 'is_archived')
    ordering = ('-created_at',)
    inlines = [ProductImageInline, ProductVideoInline]
    form = ProductAdminForm
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'price', 'stock', 'sku')
        }),
        ('Categories & Details', {
            'fields': ('category', 'brand', 'material', 'gender', 'season')
        }),
        ('Product Features', {
            'fields': ('available_sizes', 'available_colors', 'tags')
        }),
        ('Status & Ratings', {
            'fields': ('is_featured', 'is_new', 'is_on_sale', 'is_best_seller', 'average_rating', 'review_count', 'discount')
        }),
        ('Additional Information', {
            'fields': ('care_instructions', 'return_policy', 'shipping_info'),
            'classes': ('collapse',)
        }),
        ('System Fields', {
            'fields': ('created_at', 'updated_at', 'is_archived'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Override to show only non-archived products by default."""
        return super().get_queryset(request).filter(is_archived=False)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'subject', 'created_at', 'is_resolved')
    list_filter = ('subject', 'is_resolved', 'created_at', 'newsletter_signup')
    search_fields = ('first_name', 'last_name', 'email', 'message')
    readonly_fields = ('created_at',)
    list_editable = ('is_resolved',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Message Details', {
            'fields': ('subject', 'message', 'newsletter_signup')
        }),
        ('Admin Section', {
            'fields': ('is_resolved', 'admin_notes', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Show all contact messages."""
        return super().get_queryset(request)


admin.site.register(Product, ProductAdmin)