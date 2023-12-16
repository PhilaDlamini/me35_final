from BLE_CEEO import Yell, Listen
from hub import light_matrix, port
import time
import motor
import runloop

#motors
motor1 = port.A
motor2 = port.C
arm = port.E

#runs the motors
def run_motor(m, angle):
    motor.run_to_absolute_position(m, 
                    angle,                   # degrees (-180 to 180)
                    100,                  # degrees/sec
                    direction = motor.SHORTEST_PATH,   # motor.CLOCKWISE motor.COUNTERCLOCKWISE, motor.SHORTEST_PATH, motor.LONGEST_PATH
                    stop = motor.BRAKE,   # see below
                    acceleration = 1000,  # (deg/sec²) (0 - 10000)
                    deceleration = 1000)  # (deg/sec²) (0 - 10000)
    
def reset_motors():
    #reset motors
    run_motor(motor1, 0)
    run_motor(motor2, 0)
    run_motor(arm, 0)

#Connects to bluetooth and processes read data
def receive_location():
    try:
        p = Yell('Eddy', verbose = True)
        if p.connect_up():
            light_matrix.write('C')
            time.sleep(2)
            
            while True:
                
                #Process any data
                if p.is_any:
                    data = p.read()
                    print('got', data)
                    res = [int(x) for x in data.split(',')]
                    print(res)
                    
                    #move motors
                    run_motor(motor1, res[0])
                    run_motor(motor2, res[1])
                    
                    #Wait and drop arm
                    time.sleep(2)
                    run_motor(arm, 90)
                    time.sleep(2)
                    reset_motors()
                    light_matrix.write('Done')
                    
                if not p.is_connected:
                    print('lost connection')
                    break
                time.sleep(1)
    except Exception as e:
        print(e)
    finally:
        p.disconnect()
        print('closing up')
        

#the entry method of the program 
async def main():
    reset_motors()
    receive_location()

runloop.run(main())

#for MVP, send 30 and 100
