# Shortest Path Algorithm Simulator

This project is an **Advanced Data Structures** course project that simulates and visualizes shortest path routing algorithms on real-world geographical data (Pune map). The application provides a full-stack dashboard to benchmark and compare the performance, pathing, and computational efficiency of different routing algorithms.

## Features

- **Real-World Graph Data**: Uses spatial map data from Pune to calculate shortest paths.
- **Algorithm Implementations**: Includes custom implementations of four fundamental graph algorithms:
  - Dijkstra's Algorithm
  - A* Search Algorithm
  - Bellman-Ford Algorithm
  - Floyd-Warshall Algorithm (precomputed)
- **Interactive Web Interface**: A beautifully designed frontend built with HTML/CSS and JavaScript to visualize the search tree and final path on a map.
- **Benchmarking & Telemetry**: Compares distance, time taken, and nodes explored side-by-side for each algorithm.

## Technology Stack

- **Backend**: Python, Flask
- **Frontend**: Vanilla JavaScript, HTML/CSS
- **Routing Engine**: Custom algorithm implementations in Python

## Setup and Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/NotArsal/algorithm-Simulator.git
   cd algorithm-Simulator
   ```

2. **Install required dependencies**:
   Ensure you have Python installed, then run:
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the server**:
   You can run the startup script on Windows:
   ```cmd
   START_SERVER.bat
   ```
   Or run the Flask application directly:
   ```bash
   python app.py
   ```

4. **View the simulator**:
   Open your browser and navigate to `http://localhost:5000`

## Authors

- Developed for the Advanced Data Structures (ADSA) course.
