import time
from multiprocessing import Process, Queue

class ServoController(object):
    """Provide access to servo control via the ServoBlaster daemon for the Raspberry Pi"""
    
    def __init__(self, servo, lower_limit, upper_limit, sb_file, speed):
        
        self.servo = servo
        self.sb_file = sb_file
        self.lower_limit = lower_limit
        self.upper_limit = upper_limit
        self.speed = speed
        
        self.cur_pos_queue = Queue()
        self.des_pos_queue = Queue()
        self.speed_queue   = Queue()

        # Default for 'zero' position
        # Note: We create a difference between current and desired position so that we are sure
        # we have the correct position of the servo on controller initialization.  Having different
        # values for cur_pos and des_pos causes the servo to move to des_pos on startup.
        self.cur_pos = int((self.upper_limit - self.lower_limit)/2) 
        self.des_pos = self.cur_pos + 1

        # Start the subprocess for controlling this servo
        Process(target=self.start, args=()).start()

    def start(self):
        """This method should be executed in its own thread."""

        def step(increment):
            self.cur_pos += increment
            self.cur_pos_queue.put(self.cur_pos)
            self.sb_file.write('%d=%d\n' % (self.servo, self.cur_pos))
            self.sb_file.flush()
            if not self.cur_pos_queue.empty():
                trash = self.cur_pos_queue.get();

        while True:
            time.sleep(self.speed)
            # Update the current position so that it is accessible from other processes
            if self.cur_pos_queue.empty():
                self.cur_pos_queue.put(self.cur_pos)
            # Check for a position change request
            if not self.des_pos_queue.empty():
                self.des_pos = self.des_pos_queue.get()
            # Check for a speed change request
            if not self.speed_queue.empty():
                self.speed = .1 / self.speed_queue.get()
            # Move the servo if cur_pos != des_pos    
            if self.cur_pos < self.des_pos:
                step(1)
            if self.cur_pos > self.des_pos:
                step(-1)
            # We have reached the desitination position, so reduce speed so as not to waste CPU cycles
            if self.cur_pos == self.des_pos:
                self.speed = 1
                
    def move(self, position, speed):
        new_pos = position
        if new_pos > self.upper_limit:
            new_pos = self.upper_limit
        if new_pos < self.lower_limit:
            new_pos = self.lower_limit
        if new_pos != self.cur_pos:
            self.des_pos_queue.put(position)
            self.speed_queue.put(speed)        
        
    
class PanTiltController(object):
    """A class that models the control of a pan-tilt unit attached to a Raspberry Pi GPIO
       This version of the class uses the ServoBlaster servo control daemon"""

    def __init__(self, pan_servo, pan_servo_ll, pan_servo_ul, tilt_servo, tilt_servo_ll, tilt_servo_ul):
        
        """ Initialize the PanTiltController
            --------------------------------
               pan_servo      - The servo number (servoblaster) for the pan servo
               pan_servo_ll   - The PWM lower limit for the pan servo, differs from servo to servo
               pan_servo_ul   - The PWM upper limit for the pan servo, differs from servo to servo
               tilt_servo     - The servo number (servoblaster) for the tilt servo
               tilt_servo_ll  - The PWM lower limit for the tilt servo, differs from servo to servo
               tilt_servo_ul  - The PWM upper limit for the tilt servo, differs from servo to servo
        """
        
        # Open the ServoBlaster software PWM device to control the servos for the pan-tilt unit.
        self.sb_file = open('/dev/servoblaster', 'w')

        # Initialize the servos
        self.pan_servo  = ServoController(pan_servo, pan_servo_ll, pan_servo_ul, self.sb_file, .1)
        self.tilt_servo = ServoController(tilt_servo, tilt_servo_ll, tilt_servo_ul, self.sb_file, .1)

        # Wait for the servos to initialize
        time.sleep(1)
        
    
    def right(distance, speed):
        self.pan_servo.move(self.pan_servo.cur_pos + distance, speed)

    def left(distance, speed):
        self.pan_servo.move(self.pan_servo.cur_pos - distance, speed)

    def up(distance, speed):
        self.tilt_servo.move(self.tilt_servo.cur_pos - distance, speed)        

    def down(distance, speed):
        self.tilt_servo.move(self.tilt_servo.cur_pos + distance, speed)
        
        
           
    
