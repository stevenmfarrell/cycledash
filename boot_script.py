import subprocess
import time
from gpiozero import Button, LED
from pipeline import main as run_pipeline
import gpiod
import gpiodevice
from gpiod.line import Bias, Direction, Value, Edge
from datetime import timedelta
CANCELLATION_WINDOW_SECONDS = 10
LED_PIN = 13
SW_A = 5
SW_B = 6
SW_C = 16  # Set this value to '25' if you're using a Impression 13.3"
SW_D = 24
BUTTONS = [SW_A, SW_B, SW_C, SW_D]
LABELS = ["A", "B", "C", "D"]
INPUT = gpiod.LineSettings(direction=Direction.INPUT, bias=Bias.PULL_UP, edge_detection=Edge.FALLING)
chip = gpiodevice.find_chip_by_platform()
OFFSETS = [chip.line_offset_from_id(id) for id in BUTTONS]
line_config = dict.fromkeys(OFFSETS, INPUT)
request = chip.request_lines(consumer="spectra6-buttons", config=line_config)


shutdown_cancelled = False

led = chip.line_offset_from_id(LED_PIN)
gpio = chip.request_lines(consumer="inky", config={led: gpiod.LineSettings(direction=Direction.OUTPUT, bias=Bias.DISABLED)})

def led_on():
    gpio.set_value(led, Value.ACTIVE)

def led_off():
    gpio.set_value(led, Value.INACTIVE)

def handle_button(event):
    global shutdown_cancelled
    print("Button pressed! Cancellation registered.")
    shutdown_cancelled = True

def run_main_script():
    """Executes the main operational script."""
    print("Starting main script")
    try:
        run_pipeline()
        print("Main script finished successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Main script failed with error: {e}")

def shutdown_pi():
    """Powers off the Raspberry Pi."""
    print("Shutting down now.")
    subprocess.run(["sudo", "/sbin/poweroff"], check=True)


if __name__ == "__main__":
    print(f"Starting {CANCELLATION_WINDOW_SECONDS}-second cancellation window.")
    start_time = time.time()

    led_on()
    if request.wait_edge_events(timeout=timedelta(seconds=CANCELLATION_WINDOW_SECONDS)):
        request.read_edge_events() 
        shutdown_cancelled = True
        print("Button pressed! Cancellation registered.")
    led_off()

    if shutdown_cancelled:
        print("Shutdown cancelled. The Pi will remain on.")
    else:
        print("Cancellation window closed. Proceeding with script and shutdown.")
        run_main_script()
        #shutdown_pi()

