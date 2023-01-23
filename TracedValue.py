class TracedValue:
    def __init__(self, value):
        self.prev_value = None
        self.cur_value = value

    def set(self, value):
        if self.cur_value != value:
            self.prev_value = self.cur_value
            self.cur_value = value
            return 1
        else:
            return 0

    def get(self):
        return self.cur_value

    def get_diff(self):
        return self.cur_value - self.prev_value
