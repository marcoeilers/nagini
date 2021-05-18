# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

"""
Example adapted from https://bitbucket.org/covern/secc/src/master/examples/case-studies/
"""

#:: IgnoreFile(carbon)(107)

from nagini_contracts.adt import ADT
from nagini_contracts.lock import Lock
from nagini_contracts.contracts import *
from typing import NamedTuple

#enums

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
        Ensures(Acc(self.mouse_click_arg) and self.mouse_click_arg is button)
        Ensures(Acc(self.mouse_click_call) and self.mouse_click_call is call)
        Ensures(Acc(self.mouse_click_ret) and self.mouse_click_ret is domain)


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

    def __init__(self, button: Button, mouse: bool, keyboard: bool, high_key: Event, low_key: Event, et: EventType) -> None:
        self.mouse_available = mouse
        self.mouse_source = button
        self.keyboard_available = keyboard
        self.high_keyboard_source = high_key
        self.low_keyboard_source = low_key
        self.current_event_type = et
        Ensures(Acc(self.mouse_available) and self.mouse_available is mouse)
        Ensures(Acc(self.mouse_source) and self.mouse_source is button)
        Ensures(Acc(self.keyboard_available) and self.keyboard_available is keyboard)
        Ensures(Acc(self.high_keyboard_source) and self.high_keyboard_source is high_key)
        Ensures(Acc(self.low_keyboard_source) and self.low_keyboard_source is low_key)
        Ensures(Acc(self.current_event_type) and self.current_event_type is et)


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
        Ensures(Acc(self.domain_under_cursor) and self.domain_under_cursor is domain)
        Ensures(Acc(self.cursor_position) and self.cursor_position is cp)


class CompositorLock(Lock[Compositor]):

    @Predicate
    def invariant(self) -> bool:
        return (Acc(self.get_locked().domain_under_cursor) and
                Low(self.get_locked().domain_under_cursor))


# main class and methods
class CDDC:

    def __init__(self, ce: Event, b0: Event, b1: Event, ad: Domain, id: Domain,
                 hid_button: Button, hid_mouse: bool, hid_keyboard: bool, hid_high: Event, hid_low: Event, hid_et: EventType,
                 comp_domain: Domain, comp_event: Event,
                 overlay_call: bool, overlay_button: Button, overlay_domain: Domain) -> None:
        Requires(Low(overlay_call) and Low(overlay_button) and Low(overlay_domain))
        Requires(Low(hid_mouse) and Low(hid_button) and Low(hid_keyboard) and Low(hid_low))
        Requires(Low(comp_domain))
        Requires(Low(ad) and Low(id) and Low(hid_et) and Low(b0))
        self.current_event_data = ce
        self.output_event_buffer0 = b0
        self.output_event_buffer1 = b1
        self.active_domain = ad
        self.indicated_domain = id
        self.hid = HID(hid_button, hid_mouse, hid_keyboard, hid_high, hid_low, hid_et)
        self.hid_lock = HIDLock(self.hid)
        self.compositor = Compositor(comp_domain, comp_event)
        self.compositor_lock = CompositorLock(self.compositor)
        self.overlay = RPCOverlay(overlay_call, overlay_button, overlay_domain)
        self.overlay_lock = RPCOverlayLock(self.overlay)
        self.switch_state_mouse_down = False
        self.overlay_result = DomainInvalid()  # type: Domain
        Ensures(Acc(self.hid, 1 / 2) and Acc(self.hid_lock, 1 / 2) and self.hid_lock.get_locked() is self.hid and Low(self.hid_lock))
        Ensures(Acc(self.overlay, 1 / 2) and Acc(self.overlay_lock, 1 / 2) and self.overlay_lock.get_locked() is self.overlay and Low(self.overlay_lock))
        Ensures(Acc(self.compositor, 1 / 2) and Acc(self.compositor_lock, 1 / 2) and self.compositor_lock.get_locked() is self.compositor and Low(self.compositor_lock))
        Ensures(Acc(self.active_domain) and Low(self.active_domain))
        Ensures(Acc(self.indicated_domain) and Low(self.indicated_domain))
        Ensures(Acc(self.hid.current_event_type) and Low(self.hid.current_event_type))
        Ensures(Acc(self.output_event_buffer0) and Low(self.output_event_buffer0))
        Ensures(Acc(self.switch_state_mouse_down) and Low(self.switch_state_mouse_down))
        Ensures(Acc(self.overlay_result) and Low(self.overlay_result))
        Ensures(Acc(self.output_event_buffer1))
        Ensures(Acc(self.compositor.cursor_position))
        Ensures(Acc(self.current_event_data))


    def driver(self) -> None:
        Requires(Acc(self.overlay, 1 / 2) and Acc(self.overlay_lock, 1 / 2) and self.overlay_lock.get_locked() is self.overlay and Low(self.overlay_lock))
        while True:
            Invariant(Acc(self.overlay, 1 / 2) and Acc(self.overlay_lock, 1 / 2) and self.overlay_lock.get_locked() is self.overlay and Low(self.overlay_lock))
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
        Requires(Acc(self.hid, 1/2) and Acc(self.hid_lock, 1/2) and self.hid_lock.get_locked() is self.hid and Low(self.hid_lock))
        Requires(Acc(self.overlay, 1 / 2) and Acc(self.overlay_lock, 1 / 2) and self.overlay_lock.get_locked() is self.overlay and Low(self.overlay_lock))
        Requires(Acc(self.compositor, 1 / 2) and Acc(self.compositor_lock, 1 / 2) and self.compositor_lock.get_locked() is self.compositor and Low(self.compositor_lock))
        Requires(Acc(self.active_domain) and Low(self.active_domain))
        Requires(Acc(self.indicated_domain) and Low(self.indicated_domain))
        Requires(Acc(self.hid.current_event_type) and Low(self.hid.current_event_type))
        Requires(Acc(self.output_event_buffer0) and Low(self.output_event_buffer0))
        Requires(Acc(self.output_event_buffer1))
        Requires(Acc(self.compositor.cursor_position))
        Requires(Acc(self.current_event_data))
        Requires(Acc(self.switch_state_mouse_down))
        Requires(Acc(self.overlay_result))

        temp = False
        self.switch_state_mouse_down = False
        self.overlay_result = DomainInvalid()
        self.current_event_data = EventNone()
        self.indicated_domain = self.active_domain
        self.hid.current_event_type = EventTypeNone()

        while True:
            Invariant(Acc(self.hid, 1 / 2) and Acc(self.hid_lock, 1 / 2) and self.hid_lock.get_locked() is self.hid and Low(self.hid_lock))
            Invariant(Acc(self.overlay, 1 / 2) and Acc(self.overlay_lock,
                                                      1 / 2) and self.overlay_lock.get_locked() is self.overlay and Low(self.overlay_lock))
            Invariant(Acc(self.compositor, 1 / 2) and Acc(self.compositor_lock,
                                                         1 / 2) and self.compositor_lock.get_locked() is self.compositor and Low(self.compositor_lock))
            Invariant(Acc(self.overlay_result) and Low(self.overlay_result))
            Invariant(Acc(self.switch_state_mouse_down) and Low(self.switch_state_mouse_down))
            Invariant(Acc(self.current_event_data) and Low(self.current_event_data))
            Invariant(Acc(self.active_domain) and Low(self.active_domain))
            Invariant(Acc(self.indicated_domain) and self.indicated_domain is self.active_domain)
            Invariant(Acc(self.hid.current_event_type) and Low(self.hid.current_event_type))
            Invariant(Acc(self.output_event_buffer0) and Low(self.output_event_buffer0))
            Invariant(Acc(self.output_event_buffer1))
            Invariant(Acc(self.compositor.cursor_position))

            self.hid_lock.acquire()
            temp = self.hid.mouse_available
            self.hid_lock.release()

            if temp:
                self.switch_block_1()

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


    def switch_block_1(self) -> None:
        Requires(Acc(self.hid, 1 / 4) and Acc(self.hid_lock, 1 / 4) and self.hid_lock.get_locked() is self.hid and Low(self.hid_lock))
        Requires(Acc(self.overlay, 1 / 4) and Acc(self.overlay_lock, 1 / 4) and self.overlay_lock.get_locked() is self.overlay and Low(self.overlay_lock))
        Requires(Acc(self.compositor, 1 / 4) and Acc(self.compositor_lock, 1 / 4) and self.compositor_lock.get_locked() is self.compositor and Low(self.compositor_lock))
        Requires(Acc(self.overlay_result) and Low(self.overlay_result))
        Requires(Acc(self.switch_state_mouse_down) and Low(self.switch_state_mouse_down))
        Requires(Acc(self.current_event_data, 1/2) and Low(self.current_event_data))
        Requires(Acc(self.active_domain) and Low(self.active_domain))
        Requires(Acc(self.indicated_domain) and self.indicated_domain is self.active_domain)
        Requires(Acc(self.hid.current_event_type) and Low(self.hid.current_event_type))
        Requires(Acc(self.output_event_buffer0) and Low(self.output_event_buffer0))
        Requires(Acc(self.output_event_buffer1))
        Requires(Acc(self.compositor.cursor_position))
        Ensures(Acc(self.hid, 1 / 4) and Acc(self.hid_lock, 1 / 4))
        Ensures(Acc(self.overlay, 1 / 4) and Acc(self.overlay_lock, 1 / 4))
        Ensures(Acc(self.compositor, 1 / 4) and Acc(self.compositor_lock, 1 / 4))
        Ensures(Acc(self.overlay_result) and Low(self.overlay_result))
        Ensures(Acc(self.switch_state_mouse_down) and Low(self.switch_state_mouse_down))
        Ensures(Acc(self.current_event_data, 1/2))
        Ensures(Acc(self.active_domain) and Low(self.active_domain))
        Ensures(Acc(self.indicated_domain) and self.indicated_domain is self.active_domain)
        Ensures(Acc(self.hid.current_event_type) and Low(self.hid.current_event_type))
        Ensures(Acc(self.output_event_buffer0) and Low(self.output_event_buffer0))
        Ensures(Acc(self.output_event_buffer1))
        Ensures(Acc(self.compositor.cursor_position))

        cursor_domain = DomainInvalid()  # type: Domain
        self.hid.current_event_type = EventTypeMouse()
        self.hid_lock.acquire()
        source = self.hid.mouse_source
        self.hid_lock.release()

        self.overlay_lock.acquire()
        self.overlay.mouse_click_arg = source
        self.overlay.mouse_click_call = True
        self.overlay_lock.release()

        done_rpc = False

        self.switch_state_mouse_down = False

        while not done_rpc:
            Invariant(Acc(self.overlay, 1 / 8) and Acc(self.overlay_lock, 1 / 8) and self.overlay_lock.get_locked() is self.overlay and Low(self.overlay_lock))
            Invariant(Low(done_rpc) and Acc(self.overlay_result) and Low(self.overlay_result))
            self.overlay_lock.acquire()
            if not self.overlay.mouse_click_call:
                self.overlay_result = self.overlay.mouse_click_ret
                done_rpc = True
            self.overlay_lock.release()

        if self.overlay_result != DomainInvalid():
            cursor_domain = DomainOverlay()
        else:
            self.compositor.cursor_position = self.current_event_data

            self.compositor_lock.acquire()
            cursor_domain = self.compositor.domain_under_cursor
            self.compositor_lock.release()

            if cursor_domain == DomainInvalid():
                cursor_domain = self.active_domain

        if cursor_domain == DomainOverlay():
            if (self.overlay_result != DomainOverlay() and self.overlay_result != DomainInvalid()
                    and self.current_event_data == EventMouseDown()
                    and not self.switch_state_mouse_down and self.overlay_result != self.active_domain):
                self.active_domain = self.overlay_result
                self.indicated_domain = self.active_domain
        else:
            if (self.current_event_data == EventMouseDown()
                    and not self.switch_state_mouse_down
                    and cursor_domain != self.active_domain):
                self.active_domain = cursor_domain
                self.indicated_domain = self.active_domain

            if self.switch_state_mouse_down or self.current_event_data == EventMouseDown():
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
            self.switch_state_mouse_down = True
        else:
            self.switch_state_mouse_down = False