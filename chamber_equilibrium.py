# Klipper extra: chamber equilibrium gate for RatOS startup.
class ChamberEquilibrium:
    def __init__(self, config):
        self.printer = config.get_printer()
        self.gcode = self.printer.lookup_object('gcode')
        self.sensor_name = config.get('sensor', 'temperature_sensor chamber')
        self.initial_delay = config.getfloat('initial_delay', 480., minval=0.)
        self.interval = config.getfloat('interval', 300., minval=1.)
        self.target_tolerance = config.getfloat('target_tolerance', 3., minval=0.)
        self.stability_tolerance = config.getfloat('stability_tolerance', 3., minval=0.)
        self.max_wait = config.getfloat('max_wait', 5400., minval=1.)
        self.gcode.register_command('WAIT_CHAMBER_EQUILIBRIUM', self.cmd_wait)

    def cmd_wait(self, gcmd):
        target = gcmd.get_float('TARGET', minval=0.)
        sensor_name = gcmd.get('SENSOR', self.sensor_name)
        initial_delay = gcmd.get_float('INITIAL_DELAY', self.initial_delay, minval=0.)
        interval = gcmd.get_float('INTERVAL', self.interval, minval=1.)
        target_tolerance = gcmd.get_float('TARGET_TOLERANCE', self.target_tolerance, minval=0.)
        stability_tolerance = gcmd.get_float('STABILITY_TOLERANCE', self.stability_tolerance, minval=0.)
        max_wait = gcmd.get_float('MAX_WAIT', self.max_wait, minval=1.)
        sensor = self.printer.lookup_object(sensor_name)
        reactor = self.printer.get_reactor()
        started = reactor.monotonic()
        reactor.pause(started + initial_delay)
        previous = None
        while True:
            now = reactor.monotonic()
            if now - started >= max_wait:
                raise gcmd.error('Chamber equilibrium timeout after %.0f seconds' % max_wait)
            status = sensor.get_status(reactor.monotonic())
            current = status['temperature']
            gcmd.respond_info('Chamber sample %.1f C, target %.1f C' % (current, target))
            if (current >= target - target_tolerance and previous is not None
                    and abs(current - previous) <= stability_tolerance):
                gcmd.respond_info('Chamber equilibrium reached')
                return
            previous = current
            reactor.pause(min(started + max_wait, now + interval))

def load_config(config):
    return ChamberEquilibrium(config)
