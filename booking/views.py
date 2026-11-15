from decimal import Decimal
import re
from django.http import request
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction, IntegrityError
from django.contrib import messages
from django.utils import timezone
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from datetime import datetime
from django.db.models import Q
from .models import Customer, Movie, Theatre, Screen, Seat, MovieShow, ShowSeat, Booking, BookingSeat


def home(request):
    """Homepage view: retrieves movies, theatres, and shows."""
    movies = Movie.objects.all()
    theatres = Theatre.objects.all()
    now = timezone.localtime()

    shows = MovieShow.objects.filter(
        Q(show_date__gt=now.date()) |
        Q(show_date=now.date(), show_time__gt=now.time())
    ).select_related('movie', 'screen__theatre')

    context = {
        'movies': movies,
        'theatres': theatres,
        'shows': shows,
    }
    return render(request, 'home.html', context)


def movie_detail(request, movie_id):
    """
    Step 1: Movie Details Page
    Displays movie details and all upcoming theatres and shows for this movie.
    """
    movie = get_object_or_404(Movie, movie_id=movie_id)
    now = timezone.localtime()

    shows = MovieShow.objects.filter(
        Q(movie=movie) & (
            Q(show_date__gt=now.date()) |
            Q(show_date=now.date(), show_time__gt=now.time())
        )
    ).select_related('screen__theatre').order_by('show_date', 'show_time')
    # Group shows by Theatre for intuitive browsing
    theatre_shows = {}
    for show in shows:
        theatre = show.screen.theatre
        if theatre not in theatre_shows:
            theatre_shows[theatre] = []
        theatre_shows[theatre].append(show)

    context = {
        'movie': movie,
        'shows': shows,
        'theatre_shows': theatre_shows,
    }
    return render(request, 'movie_detail.html', context)


def seat_selection(request, show_id):
    """
    Step 4 & 5: Interactive Seat Selection
    Displays cinema screen layout and seats with their status (AVAILABLE / BOOKED).
    """
    show = get_object_or_404(
    MovieShow.objects.select_related('movie', 'screen__theatre'),
    show_id=show_id,
    show_date__gte=timezone.localdate()
    )  
    current_time = timezone.localtime()

    show_datetime = timezone.make_aware(
    datetime.combine(show.show_date, show.show_time)
    )

    if show_datetime <= current_time:
        messages.error(request, "Sorry, this show has already started or expired.")
        return redirect('home') 
    show_seats = (
        ShowSeat.objects.filter(show=show)
        .select_related('seat')
        .order_by('seat__seat_number')
    )

    # Group seats by row prefix (e.g. Row 'A', Row 'B')
    seat_rows = {}
    for ss in show_seats:
        seat_num = ss.seat.seat_number.strip() if ss.seat.seat_number else 'A1'
        row_letter = seat_num[0] if seat_num else 'A'
        if row_letter not in seat_rows:
            seat_rows[row_letter] = []
        seat_rows[row_letter].append(ss)

    context = {
        'show': show,
        'show_seats': show_seats,
        'seat_rows': seat_rows,
    }
    return render(request, 'seat_selection.html', context)


def booking_checkout(request):
    """
    Step 6: Booking Checkout & Customer Details
    Validates selected seats and displays order review before payment/confirmation.
    """
    if request.method == 'POST':
        show_id = request.POST.get('show_id')
        seat_ids = request.POST.getlist('seat_ids')
    else:
        show_id = request.GET.get('show_id')
        seat_ids = request.GET.getlist('seat_ids')

    if not show_id:
        messages.error(request, "No show was specified. Please choose a show.")
        return redirect('home')

    show = get_object_or_404(
    MovieShow.objects.select_related('movie', 'screen__theatre'),
    show_id=show_id,
    show_date__gte=timezone.localdate()
    )
    current_time = timezone.localtime()

    show_datetime = timezone.make_aware(
        datetime.combine(show.show_date, show.show_time)
    )

    if show_datetime <= current_time:
        messages.error(request, "Sorry, this show has already started or expired.")
        return redirect('home')

    # 1. Validate that the seat selection is non-empty
    if not seat_ids:
        messages.error(request, "Please select at least one seat to proceed.")
        return redirect('seat_selection', show_id=show.show_id)

    # 2. Sanitize and remove duplicate IDs
    try:
        clean_seat_ids = list(dict.fromkeys(
            int(s.strip()) for s in seat_ids if str(s).strip().isdigit()
        ))
    except (ValueError, TypeError):
        clean_seat_ids = []

    if not clean_seat_ids:
        messages.error(request, "Invalid seat selection format. Please choose your seats again.")
        return redirect('seat_selection', show_id=show.show_id)

    # 3. Validate that every selected ShowSeat belongs to the requested show
    selected_show_seats = list(
        ShowSeat.objects.filter(show_seat_id__in=clean_seat_ids, show=show)
        .select_related('seat')
        .order_by('seat__seat_number')
    )

    if len(selected_show_seats) != len(clean_seat_ids):
        messages.error(request, "Some selected seats do not belong to this show. Please reselect.")
        return redirect('seat_selection', show_id=show.show_id)

    # 4. Check if any seat is already booked
    unavailable_seats = [ss.seat.seat_number for ss in selected_show_seats if ss.status != 'AVAILABLE']
    if unavailable_seats:
        messages.error(
            request,
            f"Seat(s) {', '.join(unavailable_seats)} are already booked. Please choose available seats."
        )
        return redirect('seat_selection', show_id=show.show_id)

    # 5. Never trust frontend total: calculate strictly using database ticket price
    total_amount = Decimal(len(selected_show_seats)) * show.ticket_price

    context = {
        'show': show,
        'selected_show_seats': selected_show_seats,
        'clean_seat_ids_csv': ','.join(str(s) for s in clean_seat_ids),
        'seat_count': len(selected_show_seats),
        'total_amount': total_amount,
    }
    return render(request, 'booking_checkout.html', context)


def confirm_booking(request):
    """
    Step 7: Atomic Booking Transaction & Concurrency Row Locking
    Saves Customer, Booking, BookingSeat, and marks ShowSeat as BOOKED.
    """
    if request.method != 'POST':
        return redirect('home')

    show_id = request.POST.get('show_id')
    seat_ids_csv = request.POST.get('seat_ids', '')
    name = request.POST.get('name', '').strip()
    email = request.POST.get('email', '').strip().lower()
    phone = request.POST.get('phone', '').strip()

    if not show_id:
        messages.error(request, "Invalid booking request: missing show.")
        return redirect('home')

    # 1. Parse and sanitize seat IDs
    raw_ids = [s.strip() for s in seat_ids_csv.split(',') if s.strip().isdigit()]
    clean_seat_ids = list(dict.fromkeys(int(s) for s in raw_ids))

    if not clean_seat_ids:
        messages.error(request, "Your seat selection was empty or expired. Please select your seats.")
        return redirect('seat_selection', show_id=show_id)

    # 2. Server-side validation of customer inputs
    if not name or len(name) < 2 or len(name) > 100:
        messages.error(request, "Please provide a valid full name (2 to 100 characters).")
        return redirect('seat_selection', show_id=show_id)

    try:
        validate_email(email)
        if len(email) > 100:
            raise ValidationError("Email is too long.")
    except ValidationError:
        messages.error(request, "Please provide a valid email address.")
        return redirect('seat_selection', show_id=show_id)

    # Validate phone (digits, optional +, space, dash; 7-15 chars)
    phone_cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    if not phone or len(phone_cleaned) < 7 or len(phone_cleaned) > 15 or not re.match(r'^\+?[0-9]{7,15}$', phone_cleaned):
        messages.error(request, "Please provide a valid phone number (7 to 15 digits).")
        return redirect('seat_selection', show_id=show_id)

    # 3. Atomic Database Transaction with Row-Level Locking
    try:
        with transaction.atomic():
            # Retrieve show
            show = MovieShow.objects.select_for_update().get(
            show_id=show_id,
            show_date__gte=timezone.localdate()
            ) 
            # Prevent booking after the scheduled showtime
            current_time = timezone.localtime()

            show_datetime = timezone.make_aware(
                datetime.combine(show.show_date, show.show_time)
            )

            if show_datetime <= current_time:
                messages.error(request, "Sorry, this show has already started or expired.")
                return redirect('home')
  

            # Acquire exclusive row locks on the selected ShowSeat records
            # SELECT ... FROM show_seat WHERE show_seat_id IN (...) FOR UPDATE;
            locked_seats = list(
                ShowSeat.objects.select_for_update()
                .filter(show_seat_id__in=clean_seat_ids, show=show)
                .select_related('seat')
            )
            
            # Validate that all requested seat IDs exist and belong to this show
            if len(locked_seats) != len(clean_seat_ids):
                messages.error(request, "Validation error: Some seats do not belong to this show.")
                return redirect('seat_selection', show_id=show_id)

            # Validate seat availability under lock
            conflict_seats = [ss.seat.seat_number for ss in locked_seats if ss.status != 'AVAILABLE']
            if conflict_seats:
                messages.error(
                    request,
                    f"Seat(s) {', '.join(conflict_seats)} were just reserved by another customer. Please choose different seats."
                )
                return redirect('seat_selection', show_id=show_id)

            # Server-side calculation using database ticket price
            total_amount = Decimal(len(locked_seats)) * show.ticket_price

            # Correctly handle existing customers:
            # get_or_create() does not update existing records, so explicitly update name & phone!
            customer, created = Customer.objects.get_or_create(
                email=email,
                defaults={
                    'name': name,
                    'phone': phone_cleaned,
                    'created_at': timezone.now(),
                }
            )
            if not created:
                needs_update = False
                if customer.name != name:
                    customer.name = name
                    needs_update = True
                if customer.phone != phone_cleaned:
                    customer.phone = phone_cleaned
                    needs_update = True
                if needs_update:
                    customer.save(update_fields=['name', 'phone'])

            # Create Booking record
            booking = Booking.objects.create(
                customer=customer,
                show=show,
                booking_date=timezone.now(),
                total_amount=total_amount,
                booking_status='CONFIRMED',
            )

            # Insert BookingSeat records and transition ShowSeat status to BOOKED
            for show_seat in locked_seats:
                BookingSeat.objects.create(booking=booking, show_seat=show_seat)
                show_seat.status = 'BOOKED'
                show_seat.save(update_fields=['status'])

        # Outside atomic block: transaction committed successfully
        messages.success(request, f"Your reservation is confirmed! Booking Reference #{booking.booking_id}")
        return redirect('booking_success', booking_id=booking.booking_id)

    except IntegrityError:
        messages.error(
            request,
            "A concurrency collision occurred: one or more of your chosen seats were already booked. Please choose other seats."
        )
        return redirect('seat_selection', show_id=show_id)
    except MovieShow.DoesNotExist:
        messages.error(request, "This show does not exist or is no longer available for booking.")
        return redirect('home')
    except Exception as e:
        messages.error(request, f"An error occurred while confirming your reservation: {str(e)}")
        return redirect('seat_selection', show_id=show_id)


def booking_success(request, booking_id):
    """
    Step 7 (Confirmation): Digital Ticket & Boarding Pass View
    """
    booking = get_object_or_404(
        Booking.objects.select_related('customer', 'show__movie', 'show__screen__theatre'),
        booking_id=booking_id
    )
    booking_seats = (
        BookingSeat.objects.filter(booking=booking)
        .select_related('show_seat__seat')
        .order_by('show_seat__seat__seat_number')
    )

    context = {
        'booking': booking,
        'booking_seats': booking_seats,
    }
    return render(request, 'booking_success.html', context)
