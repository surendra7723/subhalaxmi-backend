from django.core.management.base import BaseCommand
from django.db import connection
from django.test.utils import override_settings
from store.models import Product
from store.views import HomeView, ProductListView, ProductDetailView
from django.test import RequestFactory
import time

class Command(BaseCommand):
    help = 'Analyze database query performance for store views'

    def add_arguments(self, parser):
        parser.add_argument(
            '--view',
            type=str,
            help='Specific view to analyze (home, list, detail)',
            choices=['home', 'list', 'detail', 'all'],
            default='all'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed query information',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database query analysis...'))
        
        factory = RequestFactory()
        
        if options['view'] in ['home', 'all']:
            self.analyze_home_view(factory, options['verbose'])
        
        if options['view'] in ['list', 'all']:
            self.analyze_list_view(factory, options['verbose'])
            
        if options['view'] in ['detail', 'all']:
            self.analyze_detail_view(factory, options['verbose'])
        
        self.stdout.write(self.style.SUCCESS('Analysis complete!'))

    def analyze_home_view(self, factory, verbose=False):
        self.stdout.write('\n=== HOME VIEW ANALYSIS ===')
        
        # Reset query log
        connection.queries_log.clear()
        
        # Create request and view
        request = factory.get('/')
        view = HomeView()
        view.setup(request)
        
        # Measure time and queries
        start_time = time.time()
        context = view.get_context_data()
        end_time = time.time()
        
        # Analyze results
        query_count = len(connection.queries)
        execution_time = end_time - start_time
        
        self.stdout.write(f'Queries executed: {query_count}')
        self.stdout.write(f'Execution time: {execution_time:.4f} seconds')
        self.stdout.write(f'Featured products: {len(context.get("featured_products", []))}')
        
        if verbose:
            self.show_queries(connection.queries)

    def analyze_list_view(self, factory, verbose=False):
        self.stdout.write('\n=== PRODUCT LIST VIEW ANALYSIS ===')
        
        # Reset query log
        connection.queries_log.clear()
        
        # Create request and view
        request = factory.get('/products/')
        view = ProductListView()
        view.setup(request)
        
        # Measure time and queries
        start_time = time.time()
        queryset = view.get_queryset()
        products = list(queryset[:12])  # Simulate pagination
        end_time = time.time()
        
        # Analyze results
        query_count = len(connection.queries)
        execution_time = end_time - start_time
        
        self.stdout.write(f'Queries executed: {query_count}')
        self.stdout.write(f'Execution time: {execution_time:.4f} seconds')
        self.stdout.write(f'Products loaded: {len(products)}')
        
        if verbose:
            self.show_queries(connection.queries)

    def analyze_detail_view(self, factory, verbose=False):
        self.stdout.write('\n=== PRODUCT DETAIL VIEW ANALYSIS ===')
        
        # Get first product for testing
        try:
            product = Product.objects.first()
            if not product:
                self.stdout.write(self.style.WARNING('No products found for testing'))
                return
        except:
            self.stdout.write(self.style.ERROR('Error fetching product for testing'))
            return
        
        # Reset query log
        connection.queries_log.clear()
        
        # Create request and view
        request = factory.get(f'/products/{product.pk}/')
        view = ProductDetailView()
        view.setup(request, pk=product.pk)
        
        # Measure time and queries
        start_time = time.time()
        view.object = view.get_object()
        context = view.get_context_data()
        end_time = time.time()
        
        # Analyze results
        query_count = len(connection.queries)
        execution_time = end_time - start_time
        
        self.stdout.write(f'Queries executed: {query_count}')
        self.stdout.write(f'Execution time: {execution_time:.4f} seconds')
        self.stdout.write(f'Product: {view.object.name}')
        self.stdout.write(f'Related products: {len(context.get("related_products", []))}')
        
        if verbose:
            self.show_queries(connection.queries)

    def show_queries(self, queries):
        self.stdout.write('\n--- SQL QUERIES ---')
        for i, query in enumerate(queries, 1):
            self.stdout.write(f'\nQuery {i} ({query["time"]}s):')
            self.stdout.write(query['sql'][:200] + ('...' if len(query['sql']) > 200 else ''))

    def compare_optimizations(self):
        """Compare before/after optimization performance"""
        self.stdout.write('\n=== OPTIMIZATION COMPARISON ===')
        
        # Test unoptimized query
        start_time = time.time()
        connection.queries_log.clear()
        
        products_unoptimized = list(Product.objects.all()[:6])
        for product in products_unoptimized:
            # Simulate template access
            list(product.images.all())
            list(product.videos.all())
        
        unoptimized_time = time.time() - start_time
        unoptimized_queries = len(connection.queries)
        
        # Test optimized query
        start_time = time.time()
        connection.queries_log.clear()
        
        products_optimized = list(Product.objects.with_media()[:6])
        for product in products_optimized:
            # Simulate template access using optimized attributes
            getattr(product, 'optimized_images', [])
            getattr(product, 'optimized_videos', [])
        
        optimized_time = time.time() - start_time
        optimized_queries = len(connection.queries)
        
        # Show comparison
        self.stdout.write(f'Unoptimized: {unoptimized_queries} queries, {unoptimized_time:.4f}s')
        self.stdout.write(f'Optimized: {optimized_queries} queries, {optimized_time:.4f}s')
        
        if unoptimized_queries > 0:
            query_improvement = ((unoptimized_queries - optimized_queries) / unoptimized_queries) * 100
            self.stdout.write(f'Query reduction: {query_improvement:.1f}%')
        
        if unoptimized_time > 0:
            time_improvement = ((unoptimized_time - optimized_time) / unoptimized_time) * 100
            self.stdout.write(f'Time improvement: {time_improvement:.1f}%')
