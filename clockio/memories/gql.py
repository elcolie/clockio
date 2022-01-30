import calendar
import copy
import datetime as dt
import typing as typ
from datetime import datetime, timezone, timedelta, time

import graphene
from django.contrib.auth import get_user_model
from graphene_django import DjangoObjectType
from graphene_django.rest_framework.mutation import SerializerMutation
from rest_framework import serializers

from clockio.memories.models import Memory, MemoryClockOut

User = get_user_model()


def today_start_stop(datetime_now: datetime = datetime.now()) -> typ.Tuple[datetime, datetime]:
    """Return tuple of start, end of today"""
    today = datetime_now.date()
    tomorrow = today + timedelta(days=1)
    today_start = datetime.combine(today, time())
    today_end = datetime.combine(tomorrow, time())
    return today_start, today_end


def work_hour_given_date(user: User, input_date: datetime) -> int:
    today_start, today_end = today_start_stop(input_date)
    clock_in_instance: Memory = Memory.objects.filter(
        user=user, clock_in__lte=today_end, clock_in__gte=today_start
    ).last()
    clock_out_instance: MemoryClockOut = MemoryClockOut.objects.filter(
        user=user, clock_out__lte=today_end, clock_out__gte=today_start
    ).last()
    if clock_out_instance is None:
        return None
    delta = clock_out_instance.clock_out - clock_in_instance.clock_in
    return delta.seconds // 3600


def get_dates_of_month(month: int) -> typ.List[dt.date]:
    """Month is int from 1 to 12."""
    now_dt = datetime.now()
    count = calendar.monthrange(now_dt.year, month)[1]
    first_day = dt.date(now_dt.year, now_dt.month, 1)
    last_day = dt.date(now_dt.year, now_dt.month, count)
    # delta = last_day - first_day
    ans = []
    running_date = copy.copy(first_day)
    while running_date <= last_day:
        ans.append(running_date)
        running_date += timedelta(days=1)
    return ans


def get_start_and_end_date_from_calendar_week(year, calendar_week) -> typ.Tuple[
    dt.date, dt.date, dt.date, dt.date, dt.date, dt.date, dt.date
]:
    """Assume work Monday to Sunday is one week."""
    monday = dt.datetime.strptime(f'{year}-{calendar_week}-1', "%Y-%W-%w").date()
    return monday, \
           monday + timedelta(days=1), \
           monday + timedelta(days=2), \
           monday + timedelta(days=3), \
           monday + timedelta(days=4), \
           monday + timedelta(days=5), \
           monday + timedelta(days=6.9)


class CurrentClockType(DjangoObjectType):
    current_clock = graphene.String()

    class Meta:
        model = Memory
        fields = [
            'current_clock',
        ]

    def resolve_current_clock(self, info) -> typ.Union[str, None]:
        today_start, today_end = today_start_stop()
        instance: Memory = Memory.objects.filter(
            user=info.context.user,
            clock_in__lte=today_end,
            clock_in__gte=today_start
        ).last()
        if instance is None:
            return None
        delta = datetime.now(timezone.utc) - instance.clock_in
        return str(delta.seconds)


class ClockedHourType(DjangoObjectType):
    today = graphene.Int()
    current_week = graphene.Int()
    current_month = graphene.Int()

    class Meta:
        model = Memory
        fields = [
            'today',
            'current_week',
            'current_month',
        ]

    def resolve_today(self, info) -> typ.Union[None, int]:
        today_start, today_end = today_start_stop()
        clock_in_instance: Memory = Memory.objects.filter(
            user=info.context.user, clock_in__lte=today_end, clock_in__gte=today_start
        ).last()
        clock_out_instance: MemoryClockOut = MemoryClockOut.objects.filter(
            user=info.context.user, clock_out__lte=today_end, clock_out__gte=today_start
        ).last()
        if clock_out_instance is None:
            return None
        delta = clock_out_instance.clock_out - clock_in_instance.clock_in
        return delta.seconds // 3600

    def resolve_current_week(self, info) -> int:
        iso_calendar = dt.datetime.now().isocalendar()
        dates = get_start_and_end_date_from_calendar_week(iso_calendar.year, iso_calendar.week)
        total_work_hours = 0
        for single_date in dates:
            work_hours_of_given_date = work_hour_given_date(
                info.context.user,
                datetime(single_date.year, single_date.month, single_date.day)
            )
            total_work_hours += work_hours_of_given_date if work_hours_of_given_date is not None else 0
        return total_work_hours

    def resolve_current_month(self, info) -> int:
        month_dates = get_dates_of_month(dt.datetime.now().month)
        total_work_hours = 0
        for single_date in month_dates:
            work_hours_of_given_date = work_hour_given_date(
                info.context.user,
                datetime(single_date.year, single_date.month, single_date.day)
            )
            total_work_hours += work_hours_of_given_date if work_hours_of_given_date is not None else 0
        return total_work_hours


class MemoryType(DjangoObjectType):
    current_clock = graphene.String()

    class Meta:
        model = Memory
        fields = [
            'clock_in',
            'current_clock',
        ]


class ClockMixin:
    def validate(self, attrs):
        if self.context['request'].user.is_anonymous:
            raise serializers.ValidationError("Please login to clockIO system!")
        return attrs

    def create(self, validated_data) -> Memory:
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class MemorySerializer(ClockMixin, serializers.ModelSerializer):
    class Meta:
        model = Memory
        fields = [
            'clock_in',
        ]
        extra_kwargs = {
            'id': {'read_only': True},
            'clock_in': {'read_only': True}
        }


class MemoryClockOutSerializer(ClockMixin, serializers.ModelSerializer):
    class Meta:
        model = MemoryClockOut
        fields = [
            'clock_out',
        ]
        extra_kwargs = {
            'id': {'read_only': True},
            'clock_out': {'read_only': True}
        }


class MemoryMutation(SerializerMutation):
    class Meta:
        serializer_class = MemorySerializer
        model_operations = ['create', ]
        lookup_field = 'id'


class MemoryClockOutMutation(SerializerMutation):
    class Meta:
        serializer_class = MemoryClockOutSerializer
        model_operations = ['create', ]
        lookup_field = 'id'
