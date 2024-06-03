# Trivia Server

A multi-threaded TCP server that serves trivia questions to clients. It allows users to select a category, difficulty level, and number of questions, and records their scores in a MySQL database.

## Features

- Handles multiple clients simultaneously using threading.
- Allows users to select trivia categories and difficulty levels.
- Fetches trivia questions from the Open Trivia Database (https://opentdb.com).
- Records user scores in a MySQL database.
- Displays a leaderboard of top scores.

## Prerequisites

- Python 3.x
- MySQL or MariaDB server
- Required Python packages: `requests`, `mysql-connector-python`

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/trivia-server.git
    cd trivia-server
    ```

2. Install the required Python packages:
    ```sh
    pip install requests mysql-connector-python
    ```

3. Configure your MySQL/MariaDB server with the following details:
    - Host: `triviadb`
    - User: `root`
    - Password: `example`
    - Database: `trivia`

4. Update the `DB_CONFIG` dictionary in the code if your database configuration is different.

## Usage

1. Set up the database by running:
    ```sh
    python server.py
    ```

2. Start the server:
    ```sh
    python server.py
    ```

3. Connect to the server using a TCP client (e.g., `telnet`):
    ```sh
    telnet localhost 2000
    ```

4. Follow the prompts to select a category, difficulty level, and number of questions.

5. Answer the trivia questions and see your score. If you are not a guest, your score will be recorded and shown on the leaderboard.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.
