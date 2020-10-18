# enums
from nagini_contracts.adt import ADT
from nagini_contracts.lock import Lock
from nagini_contracts.contracts import *
from typing import NamedTuple

class Button(ADT):
    pass

class ButtonLow(Button, NamedTuple('ButtonLow', [])):
    pass

class ButtonHigh(Button, NamedTuple('ButtonHigh', [])):
    pass

class ButtonOverlay(Button, NamedTuple('ButtonOverlay', [])):
    pass

class Domain(ADT):
    pass

class DomainLow(Domain, NamedTuple('DomainLow', [])):
    pass

class DomainHigh(Domain, NamedTuple('DomainHigh', [])):
    pass

class DomainOverlay(Domain, NamedTuple('DomainOverlay', [])):
    pass

class DomainInvalid(Domain, NamedTuple('DomainInvalid', [])):
    pass


class EventType(ADT):
    pass

class EventTypeMouse(EventType, NamedTuple('EventTypeMouse', [])):
    pass

class EventTypeNone(EventType, NamedTuple('EventTypeNone', [])):
    pass

class EventTypeKeyboard(EventType, NamedTuple('EventTypeKeyboard', [])):
    pass

class Event(ADT):
    pass

class EventNone(Event, NamedTuple('EventNone', [])):
    pass

class EventMouseDown(Event, NamedTuple('EventMouseDown', [])):
    pass

# classes and locks
class RPCOverlay:

    def __init__(self, call: bool, button: Button, domain: Domain) -> None:
        self.mouse_click_call = call
        self.mouse_click_arg = button
        self.mouse_click_ret = domain


class RPCOverlayLock(Lock[RPCOverlay]):

    @Predicate
    def invariant(self) -> bool:
        return (Acc(self.get_locked().mouse_click_call) and
                Acc(self.get_locked().mouse_click_arg) and
                Acc(self.get_locked().mouse_click_ret) and
                Low(self.get_locked().mouse_click_call) and
                Low(self.get_locked().mouse_click_arg) and
                Low(self.get_locked().mouse_click_ret))


class HID:

    def __init__(self, button: Button, mouse: int, keyboard: int, high_key: Event, low_key: Event, et: EventType) -> None:
        self.mouse_available = mouse
        self.mouse_source = button
        self.keyboard_available = keyboard
        self.high_keyboard_source = high_key
        self.low_keyboard_source = low_key
        self.current_event_type = et


class HIDLock(Lock[HID]):

    @Predicate
    def invariant(self) -> bool:
        return (Acc(self.get_locked().mouse_available) and
                Acc(self.get_locked().mouse_source) and
                Acc(self.get_locked().keyboard_available) and
                Acc(self.get_locked().high_keyboard_source) and
                Acc(self.get_locked().low_keyboard_source) and
                Low(self.get_locked().mouse_available) and
                Low(self.get_locked().mouse_source) and
                Low(self.get_locked().keyboard_available) and
                Low(self.get_locked().low_keyboard_source))


class Compositor:

    def __init__(self, domain: Domain, cp: Event) -> None:
        self.domain_under_cursor = domain
        self.cursor_position = cp


class CompositorLock(Lock[Compositor]):

    @Predicate
    def invariant(self) -> bool:
        return (Acc(self.get_locked().domain_under_cursor) and
                Low(self.get_locked().domain_under_cursor))


# main class and methods

class CDDC:

    def __init__(self, ce: Event, b0: Event, b1: Event, ad: Domain, id: Domain,
                 hid_button: Button, hid_mouse: int, hid_keyboard: int, hid_high: Event, hid_low: Event, hid_et: EventType,
                 comp_domain: Domain, comp_event: Event,
                 overlay_call: bool, overlay_button: Button, overlay_domain: Domain) -> None:
        Requires(Low(overlay_call) and Low(overlay_button) and Low(overlay_domain))
        Requires(Low(hid_mouse) and Low(hid_button) and Low(hid_keyboard) and Low(hid_low))
        Requires(Low(comp_domain))
        self.current_event_data = ce
        self.output_event_buffer0 = b0
        self.output_event_buffer1 = b1
        self.active_domain = ad
        self.indicated_domain = id
        self.hid = HID(hid_button, hid_mouse, hid_keyboard, hid_high, hid_low, hid_et)
        self.hid_lock = HIDLock(self.hid)
        self.hid_lock.release()
        self.compositor = Compositor(comp_domain, comp_event)
        self.compositor_lock = CompositorLock(self.compositor)
        self.compositor_lock.release()
        self.overlay = RPCOverlay(overlay_call, overlay_button, overlay_domain)
        self.overlay_lock = RPCOverlayLock(self.overlay)
        self.overlay_lock.release()
        Ensures(Acc(self.hid, 1 / 2) and Acc(self.hid_lock, 1 / 2) and self.hid_lock.get_locked() is self.hid)
        Ensures(Acc(self.overlay, 1 / 2) and Acc(self.overlay_lock, 1 / 2) and self.overlay_lock.get_locked() is self.overlay)
        Ensures(Acc(self.compositor, 1 / 2) and Acc(self.compositor_lock_lock, 1 / 2) and self.compositor_lock.get_locked() is self.compositor)
        Ensures(Acc(self.active_domain) and Low(self.active_domain))
        Ensures(Acc(self.indicated_domain) and Low(self.indicated_domain))
        Ensures(Acc(self.hid.current_event_type) and Low(self.hid.current_event_type))
        Ensures(Acc(self.output_event_buffer0) and Low(self.output_event_buffer0))
        Ensures(Acc(self.output_event_buffer1))
        Ensures(Acc(self.compositor.cursor_position))
        Ensures(Acc(self.current_event_data))

    def driver(self) -> None:
        Requires(Acc(self.overlay, 1 / 2) and Acc(self.overlay_lock, 1 / 2) and self.overlay_lock.get_locked() is self.overlay)
        while True:
            Invariant(Acc(self.overlay, 1 / 2) and Acc(self.overlay_lock, 1 / 2) and self.overlay_lock.get_locked() is self.overlay)
            self.overlay_lock.acquire()

            if self.overlay.mouse_click_call:
                self.overlay.mouse_click_call = False

                if self.overlay.mouse_click_arg == ButtonLow():
                    self.overlay.mouse_click_ret = DomainLow()
                elif self.overlay.mouse_click_arg == ButtonHigh():
                    self.overlay.mouse_click_ret = DomainLow()
                elif self.overlay.mouse_click_arg == ButtonOverlay():
                    self.overlay.mouse_click_ret = DomainOverlay()
                else:
                    self.overlay.mouse_click_ret = DomainInvalid()

            self.overlay_lock.release()

    def input_switch(self) -> None:
        Requires(Acc(self.hid, 1/2) and Acc(self.hid_lock, 1/2) and self.hid_lock.get_locked() is self.hid)
        Requires(Acc(self.overlay, 1 / 2) and Acc(self.overlay_lock, 1 / 2) and self.overlay_lock.get_locked() is self.overlay)
        Requires(Acc(self.compositor, 1 / 2) and Acc(self.compositor_lock_lock, 1 / 2) and self.compositor_lock.get_locked() is self.compositor)
        Requires(Acc(self.active_domain) and Low(self.active_domain))
        Requires(Acc(self.indicated_domain) and Low(self.indicated_domain))
        Requires(Acc(self.hid.current_event_type) and Low(self.hid.current_event_type))
        Requires(Acc(self.output_event_buffer0) and Low(self.output_event_buffer0))
        Requires(Acc(self.output_event_buffer1))
        Requires(Acc(self.compositor.cursor_position))
        Requires(Acc(self.current_event_data))
        temp = False
        done_rpc = False
        switch_state_mouse_down = False
        overlay_result = DomainInvalid()
        cursor_domain = DomainInvalid()
        self.current_event_data = EventNone()
        self.indicated_domain = self.active_domain
        self.hid.current_event_type = EventTypeNone()

        while True:
            Invariant(Acc(self.hid, 1 / 2) and Acc(self.hid_lock, 1 / 2) and self.hid_lock.get_locked() is self.hid)
            Invariant(Acc(self.overlay, 1 / 2) and Acc(self.overlay_lock,
                                                      1 / 2) and self.overlay_lock.get_locked() is self.overlay)
            Invariant(Acc(self.compositor, 1 / 2) and Acc(self.compositor_lock_lock,
                                                         1 / 2) and self.compositor_lock.get_locked() is self.compositor)
            Invariant(Low(overlay_result))
            Invariant(Low(switch_state_mouse_down))
            Invariant(Acc(self.current_event_data) and Low(self.current_event_data))
            Invariant(Acc(self.active_domain) and Low(self.active_domain))
            Invariant(Acc(self.indicated_domain) and Low(self.indicated_domain))
            Invariant(Acc(self.hid.current_event_type) and Low(self.hid.current_event_type))
            Invariant(Acc(self.output_event_buffer0) and Low(self.output_event_buffer0))
            Invariant(Acc(self.output_event_buffer1))
            Invariant(Acc(self.compositor.cursor_position))

            self.hid_lock.acquire()
            temp = self.hid.mouse_available
            self.hid_lock.release()

            if temp:
                self.hid.current_event_type = EventTypeMouse()
                self.hid_lock.acquire()
                source = self.hid.mouse_source
                self.hid_lock.release()

                self.overlay_lock.acquire()
                self.overlay.mouse_click_arg = source
                self.overlay.mouse_click_call = 1
                self.overlay_lock.release()

                done_rpc = False

                while not done_rpc:
                    Invariant(Low(done_rpc) and Low(overlay_result))
                    self.overlay_lock.acquire()
                    if not self.overlay.mouse_click_call:
                        overlay_result = self.overlay.mouse_click_ret
                        done_rpc = True
                    self.overlay_lock.release()

                if overlay_result != DomainInvalid():
                    cursor_domain = DomainOverlay()
                else:
                    self.compositor.cursor_position = self.current_event_data

                    self.compositor_lock.acquire()
                    cursor_domain = self.compositor.domain_under_cursor
                    self.compositor_lock.release()

                    if cursor_domain == DomainInvalid():
                        cursor_domain = self.active_domain

                if cursor_domain == DomainOverlay():
                    if (overlay_result != DomainOverlay() and overlay_result != DomainInvalid()
                            and self.current_event_data == EventMouseDown()
                            and not switch_state_mouse_down and overlay_result != self.active_domain):
                        self.active_domain = overlay_result
                        self.indicated_domain = self.active_domain
                else:
                    if (self.current_event_data == EventMouseDown()
                            and not switch_state_mouse_down
                            and cursor_domain != self.active_domain):
                        self.active_domain = cursor_domain
                        self.indicated_domain = self.active_domain

                    if switch_state_mouse_down or self.current_event_data == EventMouseDown():
                        if self.active_domain == DomainLow():
                            self.output_event_buffer0 = self.current_event_data
                        else:
                            self.output_event_buffer1 = self.current_event_data
                    else:
                        if cursor_domain == DomainLow():
                            self.output_event_buffer0 = self.current_event_data
                        else:
                            self.output_event_buffer1 = self.current_event_data

                if self.current_event_data == EventMouseDown():
                    switch_state_mouse_down = True
                else:
                    switch_state_mouse_down = False

            self.hid_lock.acquire()
            temp = self.hid.keyboard_available
            self.hid_lock.release()

            if temp:
                self.current_event_data = EventNone()
                self.hid.current_event_type = EventTypeKeyboard()

                if self.indicated_domain == DomainHigh():
                    self.hid_lock.acquire()
                    self.current_event_data = self.hid.high_keyboard_source
                    self.hid_lock.release()
                else:
                    self.hid_lock.acquire()
                    self.current_event_data = self.hid.low_keyboard_source
                    self.hid_lock.release()

                if self.active_domain == DomainLow():
                    self.output_event_buffer0 = self.current_event_data
                else:
                    self.output_event_buffer1 = self.current_event_data

            self.current_event_data = EventNone()
            self.hid.current_event_type = EventTypeNone()