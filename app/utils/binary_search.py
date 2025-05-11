from app.extensions import db
from app.models import Flight
from sqlalchemy import and_, or_, desc, asc, func
import time
import logging
import traceback
import numpy as np
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def binary_search_flights_by_price(target_price, tolerance=50.0, origin=None, destination=None, max_iterations=10, 
                                  departure_date=None, return_date=None, adaptive_tolerance=False, collect_vis_data=False):
    """
    Performs a binary search to find flights with prices close to the target price.
    
    Args:
        target_price (float): The target price to search for
        tolerance (float): Price range tolerance (+/-) around target price
        origin (str, optional): Origin airport code filter
        destination (str, optional): Destination airport code filter (can be None to search any destination)
        max_iterations (int): Maximum number of binary search iterations
        departure_date (str, optional): Filter by departure date (YYYY-MM-DD)
        return_date (str, optional): Filter by return date (YYYY-MM-DD)
        adaptive_tolerance (bool): Whether to adaptively increase tolerance if no matches found
        collect_vis_data (bool): Whether to collect data for visualization
        
    Returns:
        tuple: (matches, performance_data)
            - matches: List of flights within the target price range
            - performance_data: Dictionary with search performance metrics
    """
    # Start timer
    start_time = time.time()
    
    # Initialize tracking variables
    iterations = 0
    comparisons = 0
    search_steps = []
    
    # Ensure target_price and tolerance are floats
    target_price = float(target_price)
    initial_tolerance = float(tolerance)
    tolerance = initial_tolerance
    
    try:
        # Build the base query with additional filters if provided
        query_filters = []
        
        # Add origin and destination filters
        if origin:
            query_filters.append(Flight.departure_airport == origin.strip().upper())
        if destination and destination.strip():
            query_filters.append(Flight.arrival_airport == destination.strip().upper())
        
        # Add date filters if provided
        if departure_date:
            try:
                dep_date_obj = datetime.strptime(departure_date, '%Y-%m-%d')
                next_day = dep_date_obj + timedelta(days=1)
                # Find flights on the specified date
                query_filters.append(Flight.departure_time >= dep_date_obj)
                query_filters.append(Flight.departure_time < next_day)
            except ValueError:
                logger.warning(f"Invalid departure date format: {departure_date}, should be YYYY-MM-DD")
        
        if return_date:
            try:
                ret_date_obj = datetime.strptime(return_date, '%Y-%m-%d')
                next_day = ret_date_obj + timedelta(days=1)
                # For return flights, we could filter another condition if we have a specific return flight field
                # Here we're just logging that we received this parameter
                logger.info(f"Return date filter received: {return_date}")
            except ValueError:
                logger.warning(f"Invalid return date format: {return_date}, should be YYYY-MM-DD")
        
        # Get the min and max price boundaries from the database
        min_price_query = db.session.query(db.func.min(Flight.cost))
        max_price_query = db.session.query(db.func.max(Flight.cost))
        
        # Apply filters to boundary queries if needed
        if query_filters:
            min_price_query = min_price_query.filter(and_(*query_filters))
            max_price_query = max_price_query.filter(and_(*query_filters))
        
        min_price = min_price_query.scalar() or 0
        max_price = max_price_query.scalar() or 10000  # Fallback to a high value
        
        logger.info(f"Price range in database: £{min_price} to £{max_price}")
        
        # Check if there are any flights in the database matching filters
        if min_price == 0 and max_price == 10000:
            # No flights match the filters
            logger.warning("No flights found matching the specified filters")
            return [], {
                'iterations': 0,
                'duration_ms': 0,
                'comparisons': 0,
                'algorithm': 'binary_search',
                'min_price': None,
                'max_price': None,
                'message': 'No flights found matching the specified filters'
            }
        
        # Return early if target price is outside available range
        if target_price < min_price - tolerance or target_price > max_price + tolerance:
            logger.info(f"Target price £{target_price} is outside available range £{min_price} to £{max_price}")
            # If adaptive_tolerance is enabled, we'll continue with an adjusted tolerance
            if adaptive_tolerance:
                # Set tolerance to at least cover from min to max price
                tolerance = max(tolerance, abs(target_price - min_price), abs(target_price - max_price))
                logger.info(f"Adjusted tolerance to £{tolerance} to cover the available price range")
            else:
                return [], {
                    'iterations': 0,
                    'duration_ms': 0,
                    'comparisons': 0,
                    'algorithm': 'binary_search',
                    'min_price': min_price,
                    'max_price': max_price,
                    'message': 'Target price outside available range'
                }
        
        # Define our search boundaries
        low = min_price
        high = max_price
        
        # Track whether we've found matches
        found_matches = False
        final_matches = []
        best_matches = []
        closest_price_diff = float('inf')
        
        # Perform binary search
        while iterations < max_iterations and low <= high:
            iterations += 1
            mid_price = (low + high) / 2
            logger.info(f"Iteration {iterations}: Searching around price £{mid_price}")
            
            # Search for flights within the current price range +/- tolerance
            price_lower_bound = mid_price - tolerance
            price_upper_bound = mid_price + tolerance
            
            # Build the complete query
            query = Flight.query.filter(
                Flight.cost >= price_lower_bound,
                Flight.cost <= price_upper_bound
            )
            
            # Add additional filters
            if query_filters:
                query = query.filter(and_(*query_filters))
                
            # Get flights in the current price range
            matches = query.order_by(func.abs(Flight.cost - target_price)).all()
            comparisons += 1
            
            if collect_vis_data:
                # Record this search step for visualization
                search_steps.append({
                    'iteration': iterations,
                    'mid_price': mid_price,
                    'low': low,
                    'high': high,
                    'tolerance': tolerance,
                    'lower_bound': price_lower_bound,
                    'upper_bound': price_upper_bound,
                    'matches_found': len(matches),
                    'closest_price': matches[0].cost if matches else None
                })
            
            # Calculate how close we are to the target price
            if matches:
                # Find the match closest to the target price
                closest_match = min(matches, key=lambda f: abs(f.cost - target_price))
                current_price_diff = abs(closest_match.cost - target_price)
                
                # If we found matches and they're closer than previous ones
                if current_price_diff < closest_price_diff:
                    closest_price_diff = current_price_diff
                    best_matches = matches
                
                if current_price_diff <= tolerance:
                    # We've found a good match
                    final_matches = matches
                    found_matches = True
                    logger.info(f"Found {len(matches)} matches around price £{mid_price}")
                    # Don't break immediately, continue searching for potentially better matches
                    if current_price_diff <= tolerance * 0.2:  # If very close (within 20% of tolerance)
                        break
            
            # Adjust search boundaries based on how mid_price compares to target
            if mid_price < target_price:
                low = mid_price + 0.01  # Small increment to avoid getting stuck
            else:
                high = mid_price - 0.01  # Small decrement to avoid getting stuck
        
        # If we didn't find matches within tolerance of target and adaptive_tolerance is enabled
        if not found_matches and adaptive_tolerance:
            # Try with progressively larger tolerance until we find something
            new_tolerance = tolerance * 1.5  # Increase by 50%
            while new_tolerance <= max(max_price - min_price, tolerance * 4) and not final_matches:
                logger.info(f"No matches found with tolerance £{tolerance}. Trying with tolerance £{new_tolerance}")
                
                # Query with the new tolerance
                query = Flight.query.filter(
                    Flight.cost >= target_price - new_tolerance,
                    Flight.cost <= target_price + new_tolerance
                )
                
                # Add additional filters
                if query_filters:
                    query = query.filter(and_(*query_filters))
                
                # Execute query
                adaptive_matches = query.order_by(func.abs(Flight.cost - target_price)).all()
                
                if adaptive_matches:
                    final_matches = adaptive_matches
                    logger.info(f"Found {len(adaptive_matches)} matches with adaptive tolerance £{new_tolerance}")
                    break
                
                # Increase tolerance for next iteration
                new_tolerance *= 1.5
                # Avoid infinite loop
                if new_tolerance > 10000:
                    break
        
        # If we still didn't find matches but have some "best" ones, use those
        if not final_matches and best_matches:
            final_matches = best_matches
            logger.info(f"No exact matches found, returning {len(best_matches)} best matches")
        
        # Sort results by price (closest to target price first)
        final_matches.sort(key=lambda f: abs(f.cost - target_price))
        
        # Limit to a reasonable number
        final_matches = final_matches[:20]
        
        # Calculate performance data
        duration_ms = (time.time() - start_time) * 1000
        
        # Generate price histogram data for visualization
        histogram_data = None
        if collect_vis_data and final_matches:
            # Get all prices in the range
            price_query = db.session.query(Flight.cost)
            if query_filters:
                price_query = price_query.filter(and_(*query_filters))
            
            all_prices = [price[0] for price in price_query.all()]
            
            if all_prices:
                # Create histogram with 20 bins
                hist, bin_edges = np.histogram(all_prices, bins=20)
                histogram_data = {
                    'counts': hist.tolist(),
                    'bin_edges': bin_edges.tolist(),
                    'target_price': target_price
                }
        
        performance_data = {
            'iterations': iterations,
            'duration_ms': duration_ms,
            'comparisons': comparisons,
            'algorithm': 'binary_search',
            'min_price': min_price,
            'max_price': max_price,
            'initial_tolerance': initial_tolerance,
            'final_tolerance': tolerance,
            'search_steps': search_steps if collect_vis_data else None,
            'histogram_data': histogram_data,
            'found_exact_match': found_matches
        }
        
        return final_matches, performance_data
        
    except Exception as e:
        logger.error(f"Error in binary search: {str(e)}")
        logger.error(traceback.format_exc())
        return [], {
            'error': str(e),
            'algorithm': 'binary_search_failed'
        }

def linear_search_flights_by_price(target_price, tolerance=50.0, origin=None, destination=None, 
                                  departure_date=None, return_date=None):
    """
    Performs a linear search to find flights with prices close to the target price.
    This function is for comparison with the binary search implementation.
    
    Args:
        target_price (float): The target price to search for
        tolerance (float): Price range tolerance (+/-) around target price
        origin (str, optional): Origin airport code filter  
        destination (str, optional): Destination airport code filter
        departure_date (str, optional): Filter by departure date (YYYY-MM-DD)
        return_date (str, optional): Filter by return date (YYYY-MM-DD)
        
    Returns:
        tuple: (matches, performance_data)
            - matches: List of flights within the target price range
            - performance_data: Dictionary with search performance metrics
    """
    start_time = time.time()
    comparisons = 0
    
    # Ensure target_price is a float
    target_price = float(target_price)
    tolerance = float(tolerance)
    
    try:
        # Build query
        query = Flight.query
        
        # Add filters if provided
        if origin:
            query = query.filter(Flight.departure_airport == origin.strip().upper())
        if destination:
            query = query.filter(Flight.arrival_airport == destination.strip().upper())
        
        # Add date filters if provided
        if departure_date:
            try:
                dep_date_obj = datetime.strptime(departure_date, '%Y-%m-%d')
                next_day = dep_date_obj + timedelta(days=1)
                query = query.filter(Flight.departure_time >= dep_date_obj)
                query = query.filter(Flight.departure_time < next_day)
            except ValueError:
                logger.warning(f"Invalid departure date format: {departure_date}, should be YYYY-MM-DD")
        
        # Get all flights that match the origin/destination criteria
        all_flights = query.all()
        comparisons = 1
        
        # Filter by price range
        matches = [
            flight for flight in all_flights 
            if abs(flight.cost - target_price) <= tolerance
        ]
        
        # Sort by closest price to target
        matches.sort(key=lambda f: abs(f.cost - target_price))
        
        # Limit to a reasonable number
        matches = matches[:20]
        
        # Calculate performance metrics
        duration_ms = (time.time() - start_time) * 1000
        
        performance_data = {
            'iterations': 1,
            'duration_ms': duration_ms,
            'comparisons': comparisons,
            'algorithm': 'linear_search',
            'matches_found': len(matches)
        }
        
        return matches, performance_data
        
    except Exception as e:
        logger.error(f"Error in linear search: {str(e)}")
        logger.error(traceback.format_exc())
        return [], {
            'error': str(e),
            'algorithm': 'linear_search_failed'
        }

def compare_search_algorithms(target_price, tolerance=50.0, origin=None, destination=None, 
                            departure_date=None, return_date=None, adaptive_tolerance=False):
    """
    Compares binary search vs linear search for flight price search.
    
    Args:
        target_price (float): The target price to search for
        tolerance (float): Price range tolerance (+/-) around target price
        origin (str, optional): Origin airport code filter
        destination (str, optional): Destination airport code filter
        departure_date (str, optional): Filter by departure date (YYYY-MM-DD)
        return_date (str, optional): Filter by return date (YYYY-MM-DD)
        adaptive_tolerance (bool): Whether to adaptively increase tolerance in binary search
        
    Returns:
        dict: Comparison metrics between the two search algorithms
    """
    logger.info(f"Comparing search algorithms for target price {target_price}")
    
    # Run binary search
    binary_start = time.time()
    binary_matches, binary_perf = binary_search_flights_by_price(
        target_price, tolerance, origin, destination, 
        departure_date=departure_date, return_date=return_date, 
        adaptive_tolerance=adaptive_tolerance, collect_vis_data=True
    )
    binary_time = time.time() - binary_start
    
    # Run linear search
    linear_start = time.time()
    linear_matches, linear_perf = linear_search_flights_by_price(
        target_price, tolerance, origin, destination,
        departure_date=departure_date, return_date=return_date
    )
    linear_time = time.time() - linear_start
    
    # Prepare comparison results
    comparison = {
        'target_price': target_price,
        'tolerance': tolerance,
        'filters': {
            'origin': origin,
            'destination': destination,
            'departure_date': departure_date,
            'return_date': return_date
        },
        'binary_search': {
            'matches_found': len(binary_matches),
            'time_ms': binary_time * 1000,
            'iterations': binary_perf.get('iterations', 0),
            'comparisons': binary_perf.get('comparisons', 0),
            'search_steps': binary_perf.get('search_steps'),
            'histogram_data': binary_perf.get('histogram_data'),
            'adaptive_tolerance_used': adaptive_tolerance,
            'final_tolerance': binary_perf.get('final_tolerance')
        },
        'linear_search': {
            'matches_found': len(linear_matches),
            'time_ms': linear_time * 1000,
            'iterations': 1,
            'comparisons': linear_perf.get('comparisons', 0)
        },
        'performance_difference': {
            'time_ratio': (linear_time / binary_time) if binary_time > 0 else 0,
            'linear_is_faster': linear_time < binary_time,
            'difference_ms': abs(linear_time - binary_time) * 1000
        },
        'effectiveness': {
            'binary_search_found': len(binary_matches) > 0,
            'linear_search_found': len(linear_matches) > 0,
            'result_difference': abs(len(binary_matches) - len(linear_matches))
        }
    }
    
    # Log the results
    if comparison['performance_difference']['linear_is_faster']:
        logger.info(f"Linear search was faster by {comparison['performance_difference']['difference_ms']:.2f}ms")
    else:
        logger.info(f"Binary search was faster by {comparison['performance_difference']['difference_ms']:.2f}ms")
    
    logger.info(f"Binary search found {len(binary_matches)} matches in {binary_time*1000:.2f}ms")
    logger.info(f"Linear search found {len(linear_matches)} matches in {linear_time*1000:.2f}ms")
    
    return comparison

def binary_search_hotels_by_price(target_price, tolerance, city, check_in_date, check_out_date, guests=1, adaptive_tolerance=False, collect_vis_data=False):
    """
    Binary search for hotels by price with given criteria.
    
    Args:
        target_price (float): Target price for hotel per night in GBP
        tolerance (float): Price tolerance (±) in GBP
        city (str): Target city (IATA code)
        check_in_date (str): Check-in date (YYYY-MM-DD)
        check_out_date (str): Check-out date (YYYY-MM-DD)
        guests (int): Number of guests
        adaptive_tolerance (bool): Whether to adapt tolerance if no exact matches found
        collect_vis_data (bool): Whether to collect visualization data
    
    Returns:
        tuple: (matching_hotels, performance_data)
    """
    from flask import current_app
    from app.models import Accommodation
    from datetime import datetime
    import time
    
    logger = current_app.logger
    logger.info(f"Starting binary search for hotels: target_price=£{target_price}, tolerance=£{tolerance}, city={city}, check_in={check_in_date}, check_out={check_out_date}")
    
    # Start timing
    start_time = time.time()
    
    # Initialize performance data
    performance_data = {
        'iterations': 0,
        'search_steps': [],
        'min_price': None,
        'max_price': None,
        'initial_tolerance': tolerance,
        'final_tolerance': tolerance,
        'found_exact_match': False,
        'histogram_data': {}
    }
    
    # Convert dates to datetime objects
    try:
        check_in = datetime.strptime(check_in_date, '%Y-%m-%d')
        check_out = datetime.strptime(check_out_date, '%Y-%m-%d')
    except ValueError as e:
        logger.error(f"Date format error: {str(e)}")
        return [], performance_data
    
    # Calculate the length of stay in nights
    nights = (check_out - check_in).days
    if nights <= 0:
        logger.error("Check-out date must be after check-in date")
        return [], performance_data
    
    # Get all hotels for the city for initial search bounds
    try:
        # In a real system, you would query the database for hotels in the city
        # For this demonstration, let's create some sample hotel data
        from app.extensions import db
        
        # In a full implementation, you'd query the database
        # For now, let's create some mock hotels for demonstration
        mock_hotels = [
            {
                'id': 1,
                'name': f'Luxury Hotel in {city}',
                'address': f'{city} Downtown, 123 Main St',
                'cost_per_night': 199.99,
                'currency': 'GBP',
                'type': 'luxury',
                'rating': 4.8,
                'amenities': ['Free WiFi', 'Pool', 'Spa', 'Fitness Center', 'Restaurant'],
                'image_url': '/static/images/hotels/luxury.jpg',
                'room_type': 'Deluxe King'
            },
            {
                'id': 2,
                'name': f'Budget Inn {city}',
                'address': f'{city} Airport Area, 456 Travel Blvd',
                'cost_per_night': 89.99,
                'currency': 'GBP',
                'type': 'budget',
                'rating': 3.5,
                'amenities': ['Free WiFi', 'Free Parking', 'Continental Breakfast'],
                'image_url': '/static/images/hotels/budget.jpg',
                'room_type': 'Standard Double'
            },
            {
                'id': 3,
                'name': f'Midtown Suites {city}',
                'address': f'{city} Midtown, 789 Center Ave',
                'cost_per_night': 149.99,
                'currency': 'GBP',
                'type': 'midrange',
                'rating': 4.2,
                'amenities': ['Free WiFi', 'Kitchen', 'Laundry', 'Business Center'],
                'image_url': '/static/images/hotels/midrange.jpg',
                'room_type': 'Suite'
            },
            {
                'id': 4,
                'name': f'Hostel {city}',
                'address': f'{city} University District, 101 Student Way',
                'cost_per_night': 29.99,
                'currency': 'GBP',
                'type': 'hostel',
                'rating': 3.8,
                'amenities': ['Free WiFi', 'Shared Kitchen', 'Laundry'],
                'image_url': '/static/images/hotels/hostel.jpg',
                'room_type': 'Dorm Bed'
            },
            {
                'id': 5,
                'name': f'Business Hotel {city}',
                'address': f'{city} Financial District, 555 Commerce St',
                'cost_per_night': 179.99,
                'currency': 'GBP',
                'type': 'business',
                'rating': 4.5,
                'amenities': ['Free WiFi', 'Business Center', 'Conference Rooms', 'Restaurant'],
                'image_url': '/static/images/hotels/business.jpg',
                'room_type': 'Executive Suite'
            },
            {
                'id': 6,
                'name': f'Grand Plaza {city}',
                'address': f'{city} Plaza, 777 Grand Ave',
                'cost_per_night': 249.99,
                'currency': 'GBP',
                'type': 'luxury',
                'rating': 4.9,
                'amenities': ['Free WiFi', 'Pool', 'Spa', 'Multiple Restaurants', 'Concierge'],
                'image_url': '/static/images/hotels/grand.jpg',
                'room_type': 'Deluxe Suite'
            },
            {
                'id': 7,
                'name': f'Cozy B&B {city}',
                'address': f'{city} Historic District, 42 Heritage Lane',
                'cost_per_night': 119.99,
                'currency': 'GBP',
                'type': 'bb',
                'rating': 4.6,
                'amenities': ['Free WiFi', 'Breakfast Included', 'Garden'],
                'image_url': '/static/images/hotels/bb.jpg',
                'room_type': 'Queen Room'
            }
        ]
        
        # Sort hotels by price for binary search
        hotels = sorted(mock_hotels, key=lambda x: x['cost_per_night'])
        
        # Check if we have any hotels
        if not hotels:
            logger.warning(f"No hotels found for {city}")
            return [], performance_data
        
        # Get min and max prices
        min_price = hotels[0]['cost_per_night']
        max_price = hotels[-1]['cost_per_night']
        
        logger.info(f"Price range for hotels in {city}: £{min_price} - £{max_price}")
        performance_data['min_price'] = min_price
        performance_data['max_price'] = max_price
        
        # Collect histogram data if requested
        if collect_vis_data:
            price_ranges = {}
            range_size = (max_price - min_price) / 10 if max_price > min_price else 10
            
            for i in range(10):
                lower = min_price + i * range_size
                upper = min_price + (i + 1) * range_size
                label = f"£{lower:.2f} - £{upper:.2f}"
                price_ranges[label] = 0
            
            for hotel in hotels:
                price = hotel['cost_per_night']
                range_index = min(9, int((price - min_price) / range_size))
                lower = min_price + range_index * range_size
                upper = min_price + (range_index + 1) * range_size
                label = f"£{lower:.2f} - £{upper:.2f}"
                price_ranges[label] += 1
            
            performance_data['histogram_data'] = price_ranges
        
        # Binary search implementation
        left = 0
        right = len(hotels) - 1
        closest_match = None
        closest_diff = float('inf')
        
        while left <= right:
            performance_data['iterations'] += 1
            mid = (left + right) // 2
            current_price = hotels[mid]['cost_per_night']
            price_diff = abs(current_price - target_price)
            
            # Track search step for visualization
            if collect_vis_data:
                performance_data['search_steps'].append({
                    'iteration': performance_data['iterations'],
                    'left_index': left,
                    'right_index': right,
                    'mid_index': mid,
                    'mid_price': current_price,
                    'target_price': target_price,
                    'diff': price_diff
                })
            
            # Check if this is the closest match so far
            if price_diff < closest_diff:
                closest_match = mid
                closest_diff = price_diff
            
            # If exact match found
            if abs(current_price - target_price) <= tolerance:
                performance_data['found_exact_match'] = True
                logger.info(f"Exact match found: £{current_price:.2f} is within tolerance of target £{target_price:.2f}")
                break
            
            # Adjust search bounds
            if current_price < target_price:
                left = mid + 1
            else:
                right = mid - 1
        
        # If no exact matches found and adaptive tolerance is enabled
        if not performance_data['found_exact_match'] and adaptive_tolerance:
            # Find the appropriate tolerance to include at least one hotel
            if closest_match is not None:
                new_tolerance = closest_diff + 0.01  # Add a small buffer
                performance_data['final_tolerance'] = new_tolerance
                logger.info(f"Adaptive tolerance: increased from £{tolerance:.2f} to £{new_tolerance:.2f}")
            else:
                logger.warning("No hotels found even with adaptive tolerance")
                return [], performance_data
        
        # Gather matching hotels
        matching_hotels = []
        for hotel in hotels:
            if abs(hotel['cost_per_night'] - target_price) <= performance_data['final_tolerance']:
                matching_hotels.append(hotel)
        
        # If we found matches
        if matching_hotels:
            logger.info(f"Found {len(matching_hotels)} hotels matching the criteria")
        else:
            logger.warning(f"No hotels found matching the price criteria")
        
        # Calculate execution time
        execution_time = time.time() - start_time
        performance_data['duration_ms'] = round(execution_time * 1000, 2)
        
        return matching_hotels, performance_data
    
    except Exception as e:
        logger.error(f"Error in binary search for hotels: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return [], performance_data 