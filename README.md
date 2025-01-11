# Game Controller for ESP32 and ESP8266

This repository contains the Python-based game controller that handles the core logic for a distributed game system using ESP32 and ESP01 devices. The game involves player meeples (ESP01), control bases (ESP32), and this game controller orchestrating the actions and interactions.

---

## 📋 System Overview

- **Game Controller**: Written in Python, it orchestrates the game's flow, communicates with the ESP devices via MQTT, and manages player actions.
- **Player Control Base (ESP32)**: Equipped with an LCD screen and a button for player interactions.
- **Player Meeple (ESP01)**: Represents a player's position or state in the game.

---

## 🛠️ Requirements

To run the game controller, you need the following installed:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/install/)


Ensure your ESP32 and ESP01 are uploaded with their respective programs, and the are configured to connect to the MQTT server.

If you haven't configured your devices yet, you can find the ESP32 and ESP01 programs in the following repositories of this organization:
- [ESP32 Game Control Base](https://github.com/MEINF-Embedded-Systems/control-base-esp32)
- [ESP01 Player Meeple](https://github.com/MEINF-Embedded-Systems/meeple-eps01)


---

## 🚀 Setup and Run Instructions

1. **Clone the Repository**

   Clone this repository to your local machine:

   ```bash
   git clone <repository-url>
   cd <repository-folder>
    ```

2. **Update the Configuration**

   Update the `game-controller.py` script with your mqtt server (broker and port).

3. **Build and Run the Docker Container**

   Run the following command to build and run the Docker container:

   ```bash
   docker-compose up --build
   ```

   The game controller will start and listen for player actions.
   
