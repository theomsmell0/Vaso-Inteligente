IoT Smart Vase Project
Welcome to the repository for our IoT-enabled smart vase. This document outlines how our team developed a system to monitor plant health using common electronics and web technologies.

The core of the project is an ESP32 microcontroller that gathers data from sensors placed in the vase. This information is then transmitted to a custom online server, which processes the data and relays important updates to the user through a Telegram bot.

For local feedback, an LCD screen is attached to the vase, providing immediate status updates on whether the plant needs water or sunlight. The Telegram chat provides the same alerts, along with additional information about the specific plant you have set up.

Technology and Components
Hardware
  Microcontroller: ESP32

  Prototyping: A protoboard and jumper wires were used for the initial build. For a more stable and professional result with less signal noise, we recommend transferring the circuit to a custom     PCB (Printed Circuit Board).

  Sensors:

    Soil Humidity Sensor

    Photoresistor (LDR) for light detection

  Outputs:

    Small LED for visual status indication

    16x2 I2C LCD Display

  Power: A battery of your choice.

Software
  Editor: VSCode with the PlatformIO extension for ESP32 development.

  ESP32 Firmware: The microcontroller code is written in C++.

  Web Server: A backend server built with Flask, a Python web framework.

  Telegram Bot: The notification bot is powered by a Python script.

System Workflow
The project operates in a clear, sequential manner:

  1)Data Collection: The ESP32 continuously reads data from the soil humidity and light sensors.

  2)Data Transmission: It then sends this information to the online Flask server.

  3)Processing & Notification: The server analyzes the data to determine the plant's needs. If an action is required (e.g., watering), it triggers the Telegram bot to send a message to the user.

  4)User Interface: The user is alerted via Telegram and can also check the plant's status directly on the attached LCD display.

A Note on Language
The project was originally developed entirely in Portuguese. If you wish to adapt it to another language, you can do so by searching for the user-facing strings throughout the C++ and Python code and translating them.

Final Words
We hope this project inspires you. Good luck with your build, and we would be delighted to see what you create!

Contact:
Theo Mello - theo@mello.net.br
