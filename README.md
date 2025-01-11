# Game Controller for ESP32 and ESP8266

This repository contains the Python-based game controller that handles the core logic for a distributed game system using ESP32 and ESP8266 devices. The game involves player meeples (ESP8266), control bases (ESP32), and this game controller orchestrating the actions and interactions.

---

## 📋 System Overview

- **Game Controller**: Written in Python, it orchestrates the game's flow, communicates with the ESP devices via MQTT, and manages player actions.
- **Player Control Base (ESP32)**: Equipped with an LCD screen and a button for player interactions.
- **Player Meeple (ESP8266)**: Represents a player's position or state in the game.

---

## 🛠️ Requirements

To run the game controller, you need the following installed:

- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Python 3.10+](https://www.python.org/downloads/) (optional, if running without Docker)

Ensure your ESP32 and ESP8266 devices are flashed with the correct firmware for this game and connected to the same MQTT broker as the game controller.

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
   
