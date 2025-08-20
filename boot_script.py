import subprocess
import time
from gpiozero import Button, LED
from pipeline import main as run_pipeline
CANCELLATION_WINDOW_SECONDS = 10
BUTTON_PIN_A = 5 

LED_PIN = 6 
shutdown_cancelled = False

try:
    button_a = Button(BUTTON_PIN_A)
    led = LED(LED_PIN)
except RuntimeError as e:
    print(f"Error initializing hardware: {e}")
    exit(1)


# --- Functions ---
def handle_button_press():
    """This function is called when the button is pressed. It sets the global flag."""
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
    button_a.when_pressed = handle_button_press

    print(f"Starting {CANCELLATION_WINDOW_SECONDS}-second cancellation window.")

    led.on()

    # Wait for the window duration, checking for the button press every second
    for i in range(CANCELLATION_WINDOW_SECONDS):
        if shutdown_cancelled:
            led.off()
            break
        time.sleep(1)

    # --- End of Cancellation Window ---
    led.off()

    # --- Decide What to Do Next ---
    if shutdown_cancelled:
        # The button was pressed
        print("Shutdown cancelled. The Pi will remain on.")
    else:
        # The button was not pressed
        print("Cancellation window closed. Proceeding with script and shutdown.")
        run_main_script()
        #shutdown_pi()

