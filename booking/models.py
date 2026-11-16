# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=100)
    phone = models.CharField(max_length=15)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'customer'


class Movie(models.Model):
    def __str__(self):
        return self.title
    movie_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=150)
    genre = models.CharField(max_length=50)
    duration = models.IntegerField()
    language = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'movie'


class Theatre(models.Model):
    theatre_id = models.AutoField(primary_key=True)
    theatre_name = models.CharField(max_length=100)
    location = models.CharField(max_length=150)

    class Meta:
        managed = False
        db_table = 'theatre'


class Screen(models.Model):
    def __str__(self):
        return f"{self.screen_name} - {self.theatre.theatre_name}"
    screen_id = models.AutoField(primary_key=True)
    theatre = models.ForeignKey(Theatre, models.DO_NOTHING)
    screen_name = models.CharField(max_length=50)

    class Meta:
        managed = False
        db_table = 'screen'
        unique_together = (('theatre', 'screen_name'),)


class Seat(models.Model):
    seat_id = models.AutoField(primary_key=True)
    screen = models.ForeignKey(Screen, models.DO_NOTHING)
    seat_number = models.CharField(max_length=10)
    seat_type = models.CharField(max_length=20)

    class Meta:
        managed = False
        db_table = 'seat'
        unique_together = (('screen', 'seat_number'),)


class MovieShow(models.Model):
    show_id = models.AutoField(primary_key=True)
    movie = models.ForeignKey(Movie, models.DO_NOTHING)
    screen = models.ForeignKey(Screen, models.DO_NOTHING)
    show_date = models.DateField()
    show_time = models.TimeField()
    ticket_price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        managed = False
        db_table = 'movie_show'
        unique_together = (('screen', 'show_date', 'show_time'),)


class ShowSeat(models.Model):
    show_seat_id = models.AutoField(primary_key=True)
    show = models.ForeignKey(MovieShow, models.DO_NOTHING)
    seat = models.ForeignKey(Seat, models.DO_NOTHING)
    status = models.CharField(max_length=9, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'show_seat'
        unique_together = (('show', 'seat'),)


class Booking(models.Model):
    booking_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, models.DO_NOTHING)
    show = models.ForeignKey(MovieShow, models.DO_NOTHING)
    booking_date = models.DateTimeField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    booking_status = models.CharField(max_length=9, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'booking'


class BookingSeat(models.Model):
    booking_seat_id = models.AutoField(primary_key=True)
    booking = models.ForeignKey(Booking, models.DO_NOTHING)
    show_seat = models.OneToOneField(ShowSeat, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'booking_seat'
