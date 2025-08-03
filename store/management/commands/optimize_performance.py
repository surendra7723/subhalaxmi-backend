"""
Management command to optimize performance and check Lighthouse metrics.
"""

import time
import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.test.client import Client
from django.urls import reverse
from django.core.cache import cache
from django.db import connection
from store.models import Product


class Command(BaseCommand):
    help = 'Optimize performance and provide Lighthouse improvement suggestions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-queries',
            action='store_true',
            help='Check database query performance',
        )
        parser.add_argument(
            '--warm-cache',
            action='store_true',
            help='Warm up the cache with commonly accessed data',
        )
        parser.add_argument(
            '--compress-static',
            action='store_true',
            help='Collect and compress static files',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Run all optimizations',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting Performance Optimization...'))
        
        if options['all']:
            options['check_queries'] = True
            options['warm_cache'] = True
            options['compress_static'] = True

        if options['check_queries']:
            self.check_query_performance()
        
        if options['warm_cache']:
            self.warm_cache()
        
        if options['compress_static']:
            self.compress_static_files()
        
        self.provide_lighthouse_suggestions()
        
        self.stdout.write(self.style.SUCCESS('✅ Performance optimization completed!'))

    def check_query_performance(self):
        """Check and report database query performance."""
        self.stdout.write(self.style.HTTP_INFO('📊 Checking Database Query Performance...'))
        
        # Reset query log
        connection.queries_log.clear()
        
        # Test key pages
        client = Client()
        pages_to_test = [
            ('Homepage', '/'),
            ('Product List', reverse('store:product_list')),
        ]
        
        results = []
        for page_name, url in pages_to_test:
            start_time = time.time()
            response = client.get(url)
            end_time = time.time()
            
            query_count = len(connection.queries)
            page_load_time = (end_time - start_time) * 1000  # Convert to ms
            
            results.append({
                'page': page_name,
                'queries': query_count,
                'load_time': page_load_time,
                'status': response.status_code
            })
            
            # Reset for next page
            connection.queries_log.clear()
        
        # Display results
        self.stdout.write('\n📈 Query Performance Results:')
        for result in results:
            status_icon = '✅' if result['queries'] <= 10 and result['load_time'] <= 200 else '⚠️'
            self.stdout.write(
                f"  {status_icon} {result['page']}: "
                f"{result['queries']} queries, "
                f"{result['load_time']:.1f}ms load time"
            )
        
        # Provide recommendations
        max_queries = max(r['queries'] for r in results)
        max_load_time = max(r['load_time'] for r in results)
        
        if max_queries > 10:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  High query count detected ({max_queries}). "
                    "Consider using select_related() and prefetch_related()."
                )
            )
        
        if max_load_time > 200:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  Slow page load time detected ({max_load_time:.1f}ms). "
                    "Consider implementing caching."
                )
            )

    def warm_cache(self):
        """Warm up the cache with commonly accessed data."""
        self.stdout.write(self.style.HTTP_INFO('🔥 Warming up cache...'))
        
        try:
            # Cache featured products
            featured_products = list(Product.objects.with_media().featured()[:8])
            cache.set('featured_products', featured_products, 300)
            self.stdout.write(f"  ✅ Cached {len(featured_products)} featured products")
            
            # Cache product categories (from product.category field)
            product_categories = list(Product.objects.values_list('category', flat=True).distinct().exclude(category=''))
            cache.set('product_categories', product_categories, 600)
            self.stdout.write(f"  ✅ Cached {len(product_categories)} product categories")
            
            # Cache new arrivals
            new_arrivals = list(Product.objects.with_media().new_arrivals()[:6])
            cache.set('new_arrivals', new_arrivals, 300)
            self.stdout.write(f"  ✅ Cached {len(new_arrivals)} new arrivals")
            
            # Cache on sale products
            on_sale = list(Product.objects.with_media().on_sale()[:6])
            cache.set('on_sale_products', on_sale, 300)
            self.stdout.write(f"  ✅ Cached {len(on_sale)} on sale products")
            
            self.stdout.write(self.style.SUCCESS('🔥 Cache warmed successfully!'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Cache warming failed: {str(e)}")
            )

    def compress_static_files(self):
        """Collect and prepare static files for optimization."""
        self.stdout.write(self.style.HTTP_INFO('📦 Collecting static files...'))
        
        try:
            call_command('collectstatic', '--noinput', verbosity=0)
            self.stdout.write('  ✅ Static files collected')
            
            # Check if static files exist
            static_root = getattr(settings, 'STATIC_ROOT', None)
            if static_root and os.path.exists(static_root):
                css_files = sum(1 for _ in os.walk(static_root) if _.endswith('.css'))
                js_files = sum(1 for _ in os.walk(static_root) if _.endswith('.js'))
                self.stdout.write(f"  📊 Found {css_files} CSS and {js_files} JS files")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Static file collection failed: {str(e)}")
            )

    def provide_lighthouse_suggestions(self):
        """Provide suggestions to improve Lighthouse scores."""
        self.stdout.write(self.style.HTTP_INFO('\n🔍 Lighthouse Performance Improvement Suggestions:'))
        
        suggestions = [
            {
                'category': 'Core Web Vitals',
                'items': [
                    '🎯 Optimize Largest Contentful Paint (LCP): Ensure hero images load quickly',
                    '🎯 Minimize First Input Delay (FID): Reduce JavaScript execution time',
                    '🎯 Optimize Cumulative Layout Shift (CLS): Use proper image dimensions',
                ]
            },
            {
                'category': 'Performance Optimizations',
                'items': [
                    '⚡ Enable gzip compression (already configured in settings)',
                    '⚡ Implement lazy loading for images below the fold',
                    '⚡ Minify CSS and JavaScript files',
                    '⚡ Use WebP format for images when possible',
                    '⚡ Implement service worker for caching',
                ]
            },
            {
                'category': 'Network Optimizations',
                'items': [
                    '🌐 Use CDN for static files',
                    '🌐 Implement HTTP/2 server push for critical resources',
                    '🌐 Preload critical fonts and stylesheets',
                    '🌐 Use resource hints (dns-prefetch, preconnect)',
                ]
            },
            {
                'category': 'Code Optimizations',
                'items': [
                    '💻 Remove unused CSS and JavaScript',
                    '💻 Optimize database queries (already optimized)',
                    '💻 Implement proper caching headers',
                    '💻 Use efficient image formats and sizes',
                ]
            },
            {
                'category': 'Server Configuration',
                'items': [
                    '🖥️  Enable browser caching with proper cache headers',
                    '🖥️  Configure Brotli compression for better than gzip',
                    '🖥️  Implement Redis caching (configured but needs Redis server)',
                    '🖥️  Use a reverse proxy like Nginx for static files',
                ]
            }
        ]
        
        for suggestion_group in suggestions:
            self.stdout.write(f"\n🔸 {suggestion_group['category']}:")
            for item in suggestion_group['items']:
                self.stdout.write(f"   {item}")
        
        # Specific implementation steps
        self.stdout.write(self.style.HTTP_INFO('\n🛠️  Next Steps to Improve Your Score:'))
        steps = [
            "1. Install and start Redis server: sudo apt install redis-server",
            "2. Install image optimization packages: pip install Pillow",
            "3. Convert images to WebP format for better compression",
            "4. Set up Nginx reverse proxy for production",
            "5. Configure proper cache headers in your web server",
            "6. Implement lazy loading for product images",
            "7. Minify CSS/JS files using Django Compressor",
            "8. Enable HTTP/2 on your server",
            "9. Use a CDN service like Cloudflare",
            "10. Optimize your server response time (aim for < 200ms)",
        ]
        
        for step in steps:
            self.stdout.write(f"   {step}")
        
        self.stdout.write(self.style.SUCCESS('\n🎯 Target: These optimizations should improve your Lighthouse score from 73 to 85-95+'))
