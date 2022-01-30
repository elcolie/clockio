import datetime as dt

from django.contrib.auth import get_user_model
from freezegun import freeze_time
from graphql.error import GraphQLLocatedError
from graphql_jwt.testcases import JSONWebTokenTestCase

from clockio.memories.gql import work_hour_given_date, get_dates_of_month
from clockio.memories.models import Memory, MemoryClockOut

User = get_user_model()


def work(
    user: User,
    start_time: str = "2022-01-04 08:00:00",
    stop_time: str = "2022-01-04 18:00:00"
):
    with freeze_time(start_time):
        Memory.objects.create(user=user)
    with freeze_time(stop_time):
        MemoryClockOut.objects.create(user=user)


class MemoryTests(JSONWebTokenTestCase):
    def setUp(self):
        self.user = User.objects.create(username="test", password="aegon123")
        self.clock_in_query = """
        mutation{
          clockIn(input: {
            clientMutationId: "1111"
          }){
            errors{
              field
              messages
            }
          }
        }
        """
        self.clock_out_query = """
        mutation{
         clockOut(input:{clientMutationId: "111"}){
          errors{
              field
              messages
            }
          }
        }
        """

    def test_authenticated_user_clock_in(self) -> None:
        self.client.authenticate(self.user)
        _ = self.client.execute(self.clock_in_query)
        self.assertEqual(1, Memory.objects.count())

    def test_anonymous_clock_in(self) -> None:
        _ = self.client.execute(self.clock_in_query)
        self.assertEqual(0, Memory.objects.count())

    def test_authenticated_user_clock_out(self) -> None:
        self.client.authenticate(self.user)
        _ = self.client.execute(self.clock_out_query)
        self.assertEqual(1, MemoryClockOut.objects.count())

    def test_anonymous_clock_out(self) -> None:
        _ = self.client.execute(self.clock_out_query)
        self.assertEqual(0, MemoryClockOut.objects.count())

    def test_clock_in_and_check_current_clock(self) -> None:
        """Expect 10hr from currentClock information."""
        self.client.authenticate(self.user)
        with freeze_time("1997-07-06 08:00:12"):
            _ = self.client.execute(self.clock_in_query)
        with freeze_time("1997-07-06 18:00:12"):
            current_clock_query = """
            query{
              currentClock{
                currentClock
              }
            }
            """
            res = self.client.execute(current_clock_query)
            self.assertEqual({'currentClock': {'currentClock': '36000'}}, res.data)

    def test_clock_in_and_check_current_clock_anonymous(self) -> None:
        """Expect anonymous user not be able to query it."""
        with freeze_time("1997-07-06 08:00:12"):
            _ = self.client.execute(self.clock_in_query)
        with freeze_time("1997-07-06 18:00:12"):
            current_clock_query = """
            query{
              currentClock{
                currentClock
              }
            }
            """
            try:
                res = self.client.execute(current_clock_query)
            except GraphQLLocatedError:
                self.assertEqual({'currentClock': None}, res.data)

    def test_no_clock_in_and_check_current_clock(self) -> None:
        """Expect null from currentClock information."""
        self.client.authenticate(self.user)
        with freeze_time("1997-07-07 18:00:12"):
            current_clock_query = """
            query{
              currentClock{
                currentClock
              }
            }
            """
            res = self.client.execute(current_clock_query)
            self.assertEqual(0, Memory.objects.count())
            self.assertEqual({'currentClock': None}, res.data)

    def test_clocked_hours_today_field(self):
        self.client.authenticate(self.user)
        with freeze_time("1997-07-06 8:21:34"):
            _ = self.client.execute(self.clock_in_query)
        with freeze_time("1997-07-06 11:21:34"):
            _ = self.client.execute(self.clock_out_query)
            clocked_hours_query = """
            query{
              clockedHours{
                today
              }
            }
            """
            res = self.client.execute(clocked_hours_query)
            self.assertEqual({'clockedHours': {'today': 3}}, res.data)
            self.assertEqual(1, Memory.objects.count())
            self.assertEqual(1, MemoryClockOut.objects.count())

    def test_working_hours_given_date(self):
        self.client.authenticate(self.user)
        with freeze_time("2022-01-04 8:21:34"):
            _ = self.client.execute(self.clock_in_query)
        with freeze_time("2022-01-04 11:21:34"):
            _ = self.client.execute(self.clock_out_query)

        with freeze_time("2022-01-06 8:21:34"):
            _ = self.client.execute(self.clock_in_query)
        with freeze_time("2022-01-06 12:21:34"):
            _ = self.client.execute(self.clock_out_query)

        self.assertEqual(3, work_hour_given_date(self.user, dt.datetime(2022, 1, 4)))
        self.assertEqual(4, work_hour_given_date(self.user, dt.datetime(2022, 1, 6)))

    def test_clocked_hours_current_week(self):
        self.client.authenticate(self.user)
        with freeze_time("2022-01-04 8:21:34"):
            _ = self.client.execute(self.clock_in_query)
        with freeze_time("2022-01-04 11:21:34"):
            _ = self.client.execute(self.clock_out_query)
        with freeze_time("2022-01-06 8:21:34"):
            _ = self.client.execute(self.clock_in_query)
        with freeze_time("2022-01-06 11:21:34"):
            _ = self.client.execute(self.clock_out_query)
        with freeze_time("2022-01-07 8:21:34"):
            _ = self.client.execute(self.clock_in_query)
        with freeze_time("2022-01-07 11:21:34"):
            _ = self.client.execute(self.clock_out_query)

        with freeze_time("2022-01-07 12:00:00"):
            query = """
            query{
              clockedHours{
                currentWeek
              }
            }
            """
            res = self.client.execute(query)
            self.assertEqual({'clockedHours': {'currentWeek': 9}}, res.data)

    def test_get_dates_of_month(self) -> None:
        with freeze_time("2022-01-07 11:21:34"):
            january_dates = get_dates_of_month(1)
            self.assertEqual(31, len(january_dates))
            self.assertEqual(dt.date(2022, 1, 1), january_dates[0])
            self.assertEqual(dt.date(2022, 1, 31), january_dates[-1])

        with freeze_time("2022-02-06 11:21:34"):
            february_dates = get_dates_of_month(2)
            self.assertEqual(28, len(february_dates))
            self.assertEqual(dt.date(2022, 2, 1), february_dates[0])
            self.assertEqual(dt.date(2022, 2, 28), february_dates[-1])

        with freeze_time("2022-06-06 11:21:34"):
            june_dates = get_dates_of_month(6)
            self.assertEqual(30, len(june_dates))
            self.assertEqual(dt.date(2022, 6, 1), june_dates[0])
            self.assertEqual(dt.date(2022, 6, 30), june_dates[-1])

    def test_clocked_hours_current_week(self) -> None:
        self.client.authenticate(self.user)
        with freeze_time("2022-01-04 8:21:34"):
            _ = self.client.execute(self.clock_in_query)
        with freeze_time("2022-01-04 11:21:34"):
            _ = self.client.execute(self.clock_out_query)

        with freeze_time("2022-01-06 8:21:34"):
            _ = self.client.execute(self.clock_in_query)
        with freeze_time("2022-01-06 11:21:34"):
            _ = self.client.execute(self.clock_out_query)

        with freeze_time("2022-01-07 8:21:34"):
            _ = self.client.execute(self.clock_in_query)
        with freeze_time("2022-01-07 11:21:34"):
            _ = self.client.execute(self.clock_out_query)

        with freeze_time("2022-01-07 12:00:00"):
            query = """
            query{
              clockedHours{
                currentMonth
              }
            }
            """
            res = self.client.execute(query)
            self.assertEqual({'clockedHours': {'currentMonth': 9}}, res.data)
