"""Relógio de animação que não avança durante suspensão/orientação bloqueada."""
class ActiveTimeline:
    def __init__(self, ticks):
        self.source=ticks
        self.paused_at=None
        self.excluded=0
    def set_active(self,active):
        now=self.source()
        if not active and self.paused_at is None:self.paused_at=now
        elif active and self.paused_at is not None:
            self.excluded+=now-self.paused_at
            self.paused_at=None
    def ticks(self):
        return (self.source() if self.paused_at is None else self.paused_at)-self.excluded

