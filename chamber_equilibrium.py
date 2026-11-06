# Klipper extra: chamber warm-up monitor and stability gate.
class ChamberEquilibrium:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.sensor_name = config.get('sensor', 'temperature_sensor chamber')
        self.interval = config.getfloat('interval', 60., minval=1.)
        self.target_tolerance = config.getfloat('target_tolerance', 3., minval=0.)
        self.stability_tolerance = config.getfloat('stability_tolerance', 3., minval=0.)
        self.stability_window = config.getfloat('stability_window', 300., minval=1.)
        self.max_wait = config.getfloat('max_wait', 1800., minval=1.)
        self.heating_rate_window = config.getfloat('heating_rate_window', 300., minval=1.)
        self.heating_rate_grace = config.getfloat('heating_rate_grace', 300., minval=0.)
        self.min_heating_rate = config.getfloat('min_heating_rate', 0., minval=0.)
        self.gcode.register_command('WAIT_CHAMBER_EQUILIBRIUM', self.cmd_wait)

    def cmd_wait(self, gcmd):
        target = gcmd.get_float('TARGET', minval=0.)
        sensor_name = gcmd.get('SENSOR', self.sensor_name)
        interval = gcmd.get_float('INTERVAL', self.interval, minval=1.)
        target_tolerance = gcmd.get_float('TARGET_TOLERANCE', self.target_tolerance, minval=0.)
        stability_tolerance = gcmd.get_float('STABILITY_TOLERANCE', self.stability_tolerance, minval=0.)
        stability_window = gcmd.get_float('STABILITY_WINDOW', self.stability_window, minval=1.)
        max_wait = gcmd.get_float('MAX_WAIT', self.max_wait, minval=1.)
        heating_rate_window = gcmd.get_float('HEATING_RATE_WINDOW', self.heating_rate_window, minval=1.)
        heating_rate_grace = gcmd.get_float('HEATING_RATE_GRACE', self.heating_rate_grace, minval=0.)
        min_heating_rate = gcmd.get_float('MIN_HEATING_RATE', self.min_heating_rate, minval=0.)
        sensor = self.printer.lookup_object(sensor_name)
        reactor = self.printer.get_reactor()
        started = reactor.monotonic()
        previous = None
        samples = []
        while True:
            now = reactor.monotonic()
            elapsed = now - started
            if elapsed >= max_wait:
                raise gcmd.error('Chamber warm-up timed out after %.0f seconds at %.1f C (target %.1f C)' %
                                 (elapsed, previous[1] if previous else 0., target))
            current = sensor.get_status(now)['temperature']
            sample = (elapsed, current)
            samples.append(sample)
            minute_rate = None if previous is None else (current - previous[1]) * 60. / (elapsed - previous[0])
            window_start = elapsed - heating_rate_window
            reference = next((item for item in samples if item[0] >= window_start), None)
            window_rate = None
            if reference is not None and elapsed > reference[0]:
                window_rate = (current - reference[1]) * 60. / (elapsed - reference[0])
            details = 'Chamber %.1f C / target %.1f C' % (current, target)
            if minute_rate is not None:
                details += ', minute rate %+.2f C/min' % minute_rate
            if window_rate is not None:
                details += ', %.0f-second average %+.2f C/min' % (elapsed - reference[0], window_rate)
            gcmd.respond_info(details)

            target_reached = current >= target - target_tolerance
            if (not target_reached and elapsed >= heating_rate_grace
                    and window_rate is not None and window_rate <= min_heating_rate):
                raise gcmd.error('Chamber is not heating adequately: %.0f-second average rate is %+.2f C/min '
                                 '(minimum %.2f C/min), temperature %.1f C, target %.1f C' %
                                 (elapsed - reference[0], window_rate, min_heating_rate, current, target))

            if target_reached and elapsed >= stability_window:
                stable_reference = next((item for item in samples
                                         if item[0] >= elapsed - stability_window), None)
                if (stable_reference is not None
                        and abs(current - stable_reference[1]) <= stability_tolerance):
                    gcmd.respond_info('Chamber equilibrium reached')
                    return
            previous = sample
            reactor.pause(min(started + max_wait, now + interval))

def load_config(config):
    return ChamberEquilibrium(config)
