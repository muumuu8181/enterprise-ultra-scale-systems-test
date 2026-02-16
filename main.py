import time
from process_monitoring.reactor_monitor import ReactorMonitor
from safety_protection.scram_system import ScramSystem

def run_simulation():
    print("Initializing Nuclear Power Plant Safety System Simulation...")

    # Setup Monitors
    # Define thresholds: 300°C for Core Temp, 150 Bar for Primary Pressure
    temp_monitor = ReactorMonitor("CoreTemp", threshold=300.0)
    pressure_monitor = ReactorMonitor("PrimaryPressure", threshold=150.0)

    # Setup Safety System
    scram_system = ScramSystem()

    # Simulation Loop
    for t in range(10):
        print(f"\n--- Time Step {t} ---")

        # Simulate Normal Operation with slowly rising temperature
        current_temp = 280.0 + (t * 2)
        current_pressure = 140.0

        # Inject Fault at t=6 (High Temp event)
        if t == 6:
            print("[SIMULATION] injecting high temperature fault...")
            current_temp = 350.0 # Well above 300.0 threshold

        # Update Sensors with the simulated physical values
        temp_monitor.update_sensors(current_temp)
        pressure_monitor.update_sensors(current_pressure)

        # Check Monitors (Voting Logic happens inside here)
        temp_status = temp_monitor.check_safety_status()
        pressure_status = pressure_monitor.check_safety_status()

        print(f"Monitor Status -> Temp: {'TRIP' if temp_status else 'OK'} ({current_temp}C), Pressure: {'TRIP' if pressure_status else 'OK'}")

        # Evaluate Safety Logic
        scram_system.evaluate_monitors({
            "CoreTemp": temp_status,
            "PrimaryPressure": pressure_status
        })

        if scram_system.scram_active:
            print(">>> SAFETY SYSTEM ACTIVATED - SIMULATION HALTED")
            break

        time.sleep(0.1)

if __name__ == "__main__":
    run_simulation()
