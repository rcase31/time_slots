from datetime import timedelta, timezone, datetime


class TimeSlot(object):
    """
    >>> my_nap = TimeSlot(datetime(2019,6,4,17), 30, 5)
    >>> print(my_nap)
    04-06 17:00 [0/1]
    """
    def __init__(self, start, duration, next=None, slots=1):
        if isinstance(duration, int) or isinstance(duration, float):
            duration = timedelta(minutes=duration)
        self.start_time = start
        self.end_time = start + duration
        self.ocupation = 0
        self.capacity = slots
        self.duration = duration
        self.next = next

    def __str__(self):

        return self.start_time.strftime("%d-%m %H:%M") + ' [' + str(self.ocupation) + '/' + str(self.capacity) + ']'

    def make_appointment(self, end_time) -> bool:
        if self.ocupation >= self.capacity:
            self.ocupation = self.capacity
            return False
        else:

            if end_time != self.end_time:
                # Alô? Oi peraí que vou ver se o próximo horário também está livre...
                next_time_slot_appointment = self.next.make_appointment(end_time)
                if next_time_slot_appointment:
                    self.ocupation += 1
                    return True
                else:
                    # Caso que ocupa mais de um slot, este está livre, mas o próximo está ocupado
                    return False
            else:
                self.ocupation += 1
                return True

    def __iter__(self):
        yield 'start_time', self.start_time
        yield 'end_time', self.end_time
        yield 'ocupation', self.ocupation
        yield 'capacity', self.capacity
        yield 'duration', self.duration
        yield 'next', self.next

    def __eq__(self, other):
        return self.start_time == other.start_time

    def __lt__(self, other):
        return self.start_time < other.start_time

    def __add__(self, other):
        old_self_next = self.next
        old_other_next = other.next

        if self < other:
            if old_self_next is not None:
                self.next = other + old_self_next
            else:
                self.next = other
            return self
        else:
            if old_other_next is not None:
                other.next = self + old_other_next
            else:
                other.next = self
            return other


class TimeSlotMatrix(object):

    def __init__(self, first, venue, venue_id):
        self.venue = venue
        self.venue_id = venue_id
        self.first = first
        self.duration = first.duration
        self.time_slots = {}
        self.count = 0
        self._update_time_slots()

    def _update_time_slots(self):
        current = self.first
        while current is not None:
            self.time_slots[current.start_time] = current
            self.count += 1
            self.last = current
            current = current.next

    def get_duration(self) -> datetime:
        current = self.first
        while current.next is not None:
            current = self.first.next
        return current.end_time - self.first.start_time

    def __str__(self):

        output = str(self.venue) + '\n' + 50 * '=' + '\n'
        temp = []
        current = self.first
        while current is not None:
            temp.append(str(current))
            current = current.next
        return output + ' -> '.join(temp)

    def __eq__(self, other):
        return self.first == other.first

    def __lt__(self, other):
        return self.first < other.first

    def __add__(self, other):
        if other.count == 0:
            return self
        if self.count == 0:
            return other
        self.first += other.first
        self._update_time_slots()
        return self

    def make_appointment(self, venue_id, start, finish)->bool:
        ts = self.find_time_slot(venue_id, start)
        if ts is not None:
            return ts.make_appointment(finish)
        else:
            return False


    def find_time_slot(self, venue_id, timeslot_searched)->TimeSlot:
        """
        Return None if not found.
        :param venue_name:
        :param timeslot_searched:
        :return:
        """

        if venue_id == self.venue_id and timeslot_searched in self.time_slots.keys():
            return self.time_slots[timeslot_searched]
        else:
            return None

    def export_to_table(self):
        """

        :return: a 1-layer depth dictionary
        """
        output = []
        for slot in self.time_slots.values():
            temp_dict = dict(slot)
            temp_dict['venue_name'] = self.venue
            temp_dict['venue_id'] = self.venue_id
            output.append(temp_dict)
        return output

class TimeSlotFactory(object):
    """
    >>> start = datetime(2019, 6, 4, 9, 30)
    >>> days = 5
    >>> duration = 30 #minutes
    >>> factory = TimeSlotFactory()
    >>> first = factory.make_time_slot_sequence(start, days, duration, 7, 22, num_slots=5)
    >>> time_slot_matrix = TimeSlotMatrix(first, 'Loja Amarela', 1)
    >>> print(str(time_slot_matrix)[:100] + ' ... ' + str(time_slot_matrix)[-50:])
    Loja Amarela
    ==================================================
    04-06 09:30 [0/5] -> 04-06 10:00 [0/ ... 30 [0/5] -> 09-06 21:00 [0/5] -> 09-06 21:30 [0/5]
    """

    def _get_next_time_slot(self, end_time, duration, open_time, close_time, week_days) -> datetime:
        # making sure close corresponds to same day as ending time from reference slot
        close_time = end_time.replace(hour=close_time.hour, minute=close_time.minute)
        next_end_time = end_time + duration
        next_start_time = end_time
        if next_end_time > close_time:
            open_time_nxt_day = end_time.replace(day=end_time.day + 1, hour=open_time.hour, minute=open_time.minute)
            while open_time_nxt_day.weekday() not in week_days:
                open_time_nxt_day += timedelta(days=1)
            next_start_time = open_time_nxt_day
        return next_start_time

    def make_time_slot_sequence(self, start, days, duration, open_time, close_time, num_slots, week_days):
        if isinstance(open_time, int):
            open_time = datetime(year=start.year, month=start.month, day=start.day, hour=open_time, minute=0,
                                 tzinfo=timedelta(hours=-3))
        if isinstance(close_time, int):
            close_time = datetime(year=start.year, month=start.month, day=start.day, hour=close_time, minute=0,
                                  tzinfo=timedelta(hours=-3))
        if isinstance(days, int):
            days = timedelta(days=days)
        if isinstance(duration, int):
            duration = timedelta(minutes=duration)

        close_time_hour = timedelta(hours=close_time.hour)
        start_day = start.replace(minute=0, hour=0, second=0, microsecond=0)
        doomsday = start_day + days + close_time_hour

        first = current_slot = TimeSlot(start, duration, slots=num_slots)
        while current_slot.end_time < doomsday:
            next_time = self._get_next_time_slot(current_slot.end_time, duration, open_time, close_time, week_days)
            current_slot.next = TimeSlot(next_time, duration, slots=num_slots)
            current_slot = current_slot.next

        return first

