<div align="center">

# Mikami–Tabuchi Pathfinding Visualizer

**A web-based implementation and interactive visualization of the Mikami–Tabuchi line-search pathfinding algorithm.**

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Backend-Flask-black?logo=flask)](https://flask.palletsprojects.com/)
[![Frontend](https://img.shields.io/badge/Frontend-HTML%20%7C%20CSS%20%7C%20JavaScript-E34F26)](https://developer.mozilla.org/)
[![Domain](https://img.shields.io/badge/Domain-Pathfinding%20%7C%20VLSI%20Routing-8A2BE2)]()

</div>

---

## Overview

This project implements the **Mikami–Tabuchi line-search pathfinding algorithm** and visualizes its execution through an interactive web application. Originally developed for routing printed-circuit connections, the algorithm searches for a collision-free route by extending horizontal and vertical trial lines from both the **source (S)** and **target (T)** until the two search fronts intersect.

Unlike cell-by-cell approaches, the implementation organizes its search around line segments and their base points. A Flask backend performs grid processing, line expansion, intersection detection, and path reconstruction, while an HTML/CSS/JavaScript frontend displays the algorithm's progress.

The application is designed both as an algorithmic demonstration and as an interactive tool for understanding line-based routing.

## Key features

- **Interactive grid input:** Define empty cells, obstacles, a source, and a target.
- **Bidirectional line expansion:** Grow trial lines from the source and target.
- **Intersection detection:** Detect where the two search fronts meet.
- **Path reconstruction:** Backtrace from the intersection to recover the route.
- **Two execution modes:**
  - **Full Run** — execute the search and display the result.
  - **Step-by-Step** — advance through the algorithm one iteration at a time.
- **Multiple visualization views:**
  1. Original grid
  2. Trial-line expansion
  3. Base points
  4. Final path
- **Search statistics:** Display waypoints, explored levels, total trial lines, and the intersection point.
- **REST API:** Separate endpoints for full execution, step-wise execution, session cleanup, and server health.

## How the algorithm works

1. **Initialize:** Generate trial lines in the four directions from both the source and target.
2. **Expand:** Use points along existing trial lines as base points for generating perpendicular lines at the next level.
3. **Check intersections:** Compare source-originating and target-originating lines to identify an intersection.
4. **Reconstruct the path:** Once an intersection is found, backtrace through the parent/base-point relationships from the intersection to both endpoints.
5. **Terminate:** Return the reconstructed path, or report that no path exists when further expansion is not possible.

The implementation uses a **bottom-left origin coordinate system**: `(0, 0)` is at the bottom-left of the grid, the x-coordinate increases to the right, and the y-coordinate increases upward. Input rows are provided top-to-bottom and converted internally.

## Application preview

The application presents the original grid, trial-line propagation, base points, and final route in separate views. To make the repository preview especially useful, add screenshots or a short GIF of the running application under an `assets/` directory and embed them here.

Example:

```markdown
![Pathfinding visualizer](assets/pathfinding-demo.png)
```

## Technology stack

| Component | Technology |
|---|---|
| Algorithm and backend | Python |
| Web server and API | Flask |
| Cross-origin support | Flask-CORS |
| Frontend structure | HTML5 |
| Styling | CSS3 |
| Browser-side interaction | Vanilla JavaScript |
| Backend/frontend communication | JSON over HTTP using Fetch API |

## Repository structure

The documented application structure is:

```text
.
├── app.py
├── templates/
│   └── index.html
└── README.md
```

If your repository includes additional files (for example, sample grids, static CSS/JavaScript, screenshots, or test cases), add them to this tree so it matches the actual uploaded code.

## Getting started

### Prerequisites

- Python 3.8 or later
- `pip`

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/<your-repository>.git
cd <your-repository>
```

### 2. Install dependencies

```bash
pip install flask flask-cors
```

Alternatively, if you add a `requirements.txt` file containing the dependencies, install them with:

```bash
pip install -r requirements.txt
```

### 3. Start the application

```bash
python app.py
```

The Flask development server should start locally. Open the URL printed in the terminal, typically:

```text
http://127.0.0.1:5000
```

Use `Ctrl+C` in the terminal to stop the server.

> **Note:** The Flask development server is intended for local development and demonstration, not production deployment.

## Providing a grid

Enter a comma-separated grid in the web interface. Each cell uses the following notation:

| Symbol | Meaning |
|---|---|
| `0` | Empty / traversable cell |
| `1` | Obstacle |
| `S` | Source |
| `T` | Target |

Example input:

```text
0,0,0,0,0,1,0,0,0,0
0,0,0,0,0,0,0,0,0,0
0,0,1,0,1,0,0,1,0,0
0,0,0,0,0,0,0,0,0,1
0,1,0,0,0,0,0,0,T,0
0,0,0,0,0,0,0,0,0,0
1,S,0,1,0,0,0,0,0,0
0,0,0,0,0,1,0,0,0,0
```

Place exactly one `S` and one `T` in the grid, and use consistent row lengths. Select **Full Run** or **Step-by-Step**, then choose **Solve**.

## API endpoints

The Flask backend exposes the following endpoints, as documented in the project report:

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/solve` | Execute the complete algorithm and return the result. |
| `POST` | `/solve/init` | Initialize a step-by-step session. |
| `POST` | `/solve/step` | Advance an existing session by one iteration. |
| `POST` | `/solve/cleanup` | End a session and release its resources. |
| `GET` | `/health` | Check server status. |

The full-run endpoint accepts JSON containing `grid_data`. The step-by-step flow uses a `session_id` returned during initialization.

The result data can include:

- `success`
- `path`
- `waypoints`
- `levels_explored`
- `intersection_point`
- `total_trial_lines`
- `step_history`
- `grid`
- `start_pos`
- `target_pos`

Refer to `app.py` for the exact request and response schemas implemented in the current code.

## Reported experimental results

The project report includes the following grid-size experiments:

| Grid size | Obstacles | Execution time (ms) | Trial lines |
|---:|---:|---:|---:|
| 5 × 5 | 3 | 15 | 12 |
| 10 × 10 | 15 | 45 | 38 |
| 15 × 15 | 35 | 112 | 67 |
| 20 × 20 | 60 | 198 | 94 |
| 25 × 25 | 95 | 324 | 128 |

These are the measurements reported in the project document. They are included as reference results; execution time can vary with hardware, grid layout, and implementation changes. The report also demonstrates successful path discovery and a no-path scenario.

## Project documentation

The repository can include the accompanying project documents:

- **Project report:** implementation details, algorithm foundations, architecture, API design, test scenarios, and performance analysis.
- **Project presentation:** project objective, system architecture, frontend walkthrough, backend implementation, and result observations.

If you upload these documents into a `docs/` directory, link them here, for example:

- [Project Report](docs/REPORT.pdf)
- [Project Presentation](docs/PROJECT_PRESENTATION.pdf)

## Team

Developed as a team project for **Computer-Aided Design for IC Design** at **Vellore Institute of Technology (VIT), Chennai**.

- **Harsh Vardhan Singh**
- Garvit Maheshwari
- Adish Vipin
- Tanmay Sharma


## Potential extensions

The project report identifies several possible future directions:

- Weighted pathfinding and multi-criteria routing.
- Multi-target routing.
- Dynamic obstacle handling and route adaptation.
- Further evaluation across larger and more varied grid configurations.

## Disclaimer

This repository is an academic implementation and visualization project. The reported behavior and performance correspond to the test scenarios described in the project documentation; they should not be interpreted as a guarantee of optimality or performance for every possible grid or routing problem.

---

<div align="center">

**Mikami–Tabuchi Line Search · Interactive Pathfinding · VLSI Routing**

</div>
