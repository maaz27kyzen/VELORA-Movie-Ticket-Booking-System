from django.contrib import admin
from .models import (
    Customer,
    Movie,
    Theatre,
    Screen,
    Seat,
    MovieShow,
    ShowSeat,
    Booking,
    BookingSeat,
)


# --------------------------------
# MOVIE MANAGEMENT
# --------------------------------

@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ('movie_id', 'title', 'genre', 'duration')
    search_fields = ('title', 'genre')
    ordering = ('title',)


# --------------------------------
# THEATRE MANAGEMENT
# --------------------------------

@admin.register(Theatre)
class TheatreAdmin(admin.ModelAdmin):
    list_display = ('theatre_id', 'theatre_name', 'location')
    search_fields = ('theatre_name',)
    ordering = ('theatre_name',)


# --------------------------------
# SCREEN MANAGEMENT
# --------------------------------

admin.site.register(Screen)


# --------------------------------
# SEAT MANAGEMENT
# --------------------------------

admin.site.register(Seat)


# --------------------------------
# SHOW MANAGEMENT
# --------------------------------

@admin.register(MovieShow)
class MovieShowAdmin(admin.ModelAdmin):
    list_display = (
        'show_id',
        'movie',
        'show_date',
        'show_time',
    )
    list_filter = ('show_date',)
    search_fields = ('movie__title',)
    ordering = ('show_date', 'show_time')

    def save_model(self, request, obj, form, change):
        # Save the movie show first
        super().save_model(request, obj, form, change)

        # Get all physical seats belonging to the selected screen
        screen_seats = Seat.objects.filter(screen=obj.screen)

        # Find existing seat records for this show
        existing_seat_ids = ShowSeat.objects.filter(
            show=obj
        ).values_list('seat_id', flat=True)

        # Identify seats that do not yet have a ShowSeat record
        new_show_seats = [
            ShowSeat(
                show=obj,
                seat=seat,
                status='AVAILABLE'
            )
            for seat in screen_seats
            if seat.seat_id not in existing_seat_ids
        ]

        # Create all missing seat records
        if new_show_seats:
            ShowSeat.objects.bulk_create(
                new_show_seats,
                ignore_conflicts=True
            )


# --------------------------------
# READ-ONLY RECORDS
# --------------------------------

class ReadOnlyAdmin(admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Customer)
class CustomerAdmin(ReadOnlyAdmin):
    list_display = ('customer_id', 'name', 'email', 'phone')
    search_fields = ('name', 'email')


@admin.register(ShowSeat)
class ShowSeatAdmin(ReadOnlyAdmin):
    list_display = ('show_seat_id', 'show', 'seat', 'status')
    list_filter = ('status',)


@admin.register(Booking)
class BookingAdmin(ReadOnlyAdmin):

    list_display = (
        'booking_id',
        'customer_name',
        'movie_title',
        'booking_date',
        'total_amount',
        'booking_status',
    )

    list_filter = ('booking_status', 'booking_date')
    search_fields = ('customer__name', 'customer__email')

    @admin.display(description='Customer')
    def customer_name(self, obj):
        return obj.customer.name

    @admin.display(description='Movie')
    def movie_title(self, obj):
        return obj.show.movie.title


@admin.register(BookingSeat)
class BookingSeatAdmin(ReadOnlyAdmin):
    list_display = ('booking_seat_id', 'booking', 'show_seat')