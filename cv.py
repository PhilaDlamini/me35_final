import cv2
import numpy as np
import time
import tinyik
import asyncio
import sys

from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

# bleak BLE
UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

async def uart(name = 'Eddy', angle = ''):
    """This sends info back and forth"""
    names = []
    def match_name(device, adv):
        if not adv.local_name in names:
            names.append(adv.local_name) #make a list of all BLE devices seen
            print(adv.local_name)
        return adv.local_name == name #is this the right one?

    device = await BleakScanner.find_device_by_filter(match_name)

    if device is None:
        print("no matching device found, check the name.")
        sys.exit(1)

    def handle_disconnect(_: BleakClient):
        print("Device was disconnected, goodbye.")
        # cancelling all tasks effectively ends the program
        for task in asyncio.all_tasks():
            task.cancel()

    def handle_rx(_: BleakGATTCharacteristic, data: bytearray):
        print("received:", data)

    async with BleakClient(device, disconnected_callback=handle_disconnect) as client:
        await client.start_notify(UART_TX_CHAR_UUID, handle_rx)

        loop = asyncio.get_running_loop()
        service = client.services.get_service(UART_SERVICE_UUID)
        rx_char = service.get_characteristic(UART_RX_CHAR_UUID)
        
        data = angle
        await client.write_gatt_char(rx_char, data.encode('UTF-8'), response=False)
        print("sent:", data)
        await asyncio.sleep(3)

# Left Upper Corner is (0,0)
# 1080 * 1900

# Define tinyik
arm = tinyik.Actuator(['z', [623., 0., 0.], 'z', [374., 0., 0.]])

# Function to get coordinate and draw lines and text
def draw_coordinate_info(image, coordinate):
    # Add text displaying coordinates
    cv2.putText(image, f"Coordinates: {coordinate}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

# Function to get coordinate of a point in an image with purple color
def get_purple_coordinate(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define lower and upper bounds for purple color in HSV
    lower_purple = np.array([130, 50, 50])
    upper_purple = np.array([160, 255, 255])

    # Threshold the HSV image to get only purple colors
    mask = cv2.inRange(hsv, lower_purple, upper_purple)

    # Find contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Initialize variables for the contour with the largest area
    max_contour = None
    max_area = 0

    # Iterate through contours
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > max_area:
            max_area = area
            max_contour = contour

    if max_contour is not None:
        # Calculate the bounding box around the largest purple contour
        x, y, w, h = cv2.boundingRect(max_contour)
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Calculate the centroid of the largest purple contour
        M = cv2.moments(max_contour)
        if M["m00"] != 0:
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])

            # Subtract the centroid coordinates from the width and height of the frame
            cX = image.shape[1] - cX
            cY = image.shape[0] - cY
            cv2.circle(image, (cX, cY), 5, (255, 0, 0), -1)
            return (cX, cY)

    return None

# Define a video capture object and start image
vid = cv2.VideoCapture(0)

send = ''
count = 0
npresult1 = 30
npresult2 = 100

try:
    while True:

        count += 1

        # Capture frame-by-frame
        ret, frame = vid.read()

        coordinate = get_purple_coordinate(frame)

        # Call the function to draw coordinate information
        draw_coordinate_info(frame, coordinate)

        # Display the frame
        cv2.imshow("Frame", frame)

        if coordinate is not None:
            print("Coordinate:", coordinate)
            arm.ee = [coordinate[0], coordinate[1], 0.]
            npresult1 = np.round(np.rad2deg(arm.angles[0]))
            npresult2 = np.round(np.rad2deg(arm.angles[1]))

        send = str(int(npresult1))+','+str(int(npresult2))
        cheat = str(int(30))+','+str(int(100))
        # print(send)

        if arm.angles.any() and count > 100:
            asyncio.run(uart('Eddy', send))
            # asyncio.run(uart('Fred', cheat))
            break     

        # Break the loop if 'q' key is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    # Release the VideoCapture and close all windows on keyboard interrupt
    print('Keyboard interrupt')
finally:
    # Release the VideoCapture and close all windows    
    vid.release()
    cv2.destroyAllWindows()