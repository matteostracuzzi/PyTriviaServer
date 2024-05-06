from socketserver import TCPServer, StreamRequestHandler, ThreadingMixIn  # Import necessary modules
import requests  # For making HTTP requests
import logging  # For logging errors
import random  # For shuffling options
import mysql.connector
from html import unescape
# Configure logging to show debug messages
logging.basicConfig(level=logging.DEBUG)

# Database configuration
DB_CONFIG = {
    'host': 'triviadb',
    'user': 'root',
    'password': 'example',
    'database': 'trivia'
}

# Define a custom TCP server class for handling trivia requests
class TriviaServer(ThreadingMixIn, TCPServer):
    pass

# Define a custom request handler for trivia requests
class TriviaHandler(StreamRequestHandler):
    # Dictionary mapping category codes to category names
    CATEGORIES = {
        "Any": "Any Category",
        "9": "General Knowledge",
        "10": "Entertainment: Books",
        "11": "Entertainment: Film",
        "12": "Entertainment: Music",
        "13": "Entertainment: Musicals & Theatres",
        "14": "Entertainment: Television",
        "15": "Entertainment: Video Games",
        "16": "Entertainment: Board Games",
        "17": "Science & Nature",
        "18": "Science: Computers",
        "19": "Science: Mathematics",
        "20": "Mythology",
        "21": "Sports",
        "22": "Geography",
        "23": "History",
        "24": "Politics",
        "25": "Art",
        "26": "Celebrities",
        "27": "Animals",
        "28": "Vehicles",
        "29": "Entertainment: Comics",
        "30": "Science: Gadgets",
        "31": "Entertainment: Japanese Anime & Manga",
        "32": "Entertainment: Cartoon & Animations"
    }

    # Method to select a category
    def select_category(self):
        self.wfile.write(b"Select the category:\n")
        for code, name in self.CATEGORIES.items():
            self.wfile.write(f"\t{code}: {name}\n".encode())
        msg = self.rfile.readline().strip().decode()
        if msg not in self.CATEGORIES:
            self.wfile.write(b"Invalid category\n")
            self.select_category()
        else:
            self.category = msg
        logging.debug("Selected category: %s", self.category)

    # Method to select a difficulty level
    def select_level(self):
        self.wfile.write(b"Select the level:\n")
        self.wfile.write(b"\t1 - easy\n")
        self.wfile.write(b"\t2 - medium\n")
        self.wfile.write(b"\t3 - hard\n")
        msg = self.rfile.readline().strip().decode()
        if msg not in ["1", "2", "3"]:
            self.wfile.write(b"Invalid level\n")
            self.select_level()
        else:
            self.level = int(msg)

    # Method to select the number of questions
    def select_amount(self):
        self.wfile.write(b"Select the amount:\n")
        msg = self.rfile.readline().strip().decode()
        try:
            amount = int(msg)
            if amount <= 0:
                raise ValueError
            self.amount = amount
        except ValueError:
            self.wfile.write(b"Invalid amount\n")
            self.select_amount()

    # Method to retrieve trivia questions from an API
    def retrieve_questions(self):
        difficulty = ["easy", "medium", "hard"]
        api_url = "https://opentdb.com/api.php"
        params = {
            "amount": self.amount,
            "difficulty": difficulty[self.level - 1],
        }
        if self.category != "Any":
            params["category"] = self.category
        response = requests.get(api_url, params=params)

        if response.status_code == 200:
            data = response.json()
            self.questions = data.get("results", [])
        else:
            logging.error("Failed to fetch trivia questions. Status code: %s", response.status_code)

    # Method to retrieve a nickname from the client
    def retrieve_nickname(self):
        blacklist = ["hitler", "botti", "guest", "anonimo", "ospite"]
        self.wfile.write(b"Who are you?\n")
        data = self.rfile.readline().strip().decode()
        if not data:
            return False
        self.nickname = data.split()[0]
        if self.nickname.lower() in blacklist:
            self.wfile.write(b"Invalid nickname, entering as guest\n")
            return False
        return True

    # Method to display a trivia question and handle user responses
    def display_question(self, question):
        self.wfile.write(f"\nQuestion: {unescape(question['question'])}\n".encode())
        options = question["incorrect_answers"] + [question["correct_answer"]]
        random.shuffle(options)
        for idx, option in enumerate(options):
            self.wfile.write(f"{idx + 1}. {unescape(option)}\n".encode())
        self.wfile.write(b"Choose the correct option: ")
        answer = self.rfile.readline().strip().decode()
        if answer not in ["1", "2", "3", "4"]:
            self.wfile.write(b"Invalid choice. Please choose again.\n")
            self.display_question(question)
        elif options[int(answer) - 1] == question["correct_answer"]:
            self.wfile.write(b"Correct!\n")
            self.score += 1
        else:
            self.wfile.write(f"Wrong! The correct answer is: {question['correct_answer']}\n".encode())
        self.wfile.write(f"Your current score: {self.score}\n".encode())

    def update_scores(self):
        try:
            # Establish a connection to the database
            connection = mysql.connector.connect(**DB_CONFIG)
            if connection.is_connected():
                cursor = connection.cursor()
                cursor.execute('SELECT * FROM players WHERE nickname = %s;',(self.nickname))
                player = cursor.fetchone()
                if not player:
                    cursor.execute('INSERT INTO players (nickname, score) VALUES (%s, %d);',(self.nickname, self.score))
                    connection.commit()
                elif player[0]["score"] < self.score:
                    cursor.execute('UPDATE players SET score = %d WHERE nickname = %s;',(self.score,self.nickname))
                    connection.commit()

        except mysql.connector.Error as e:
            logging.error("Error while connecting to MariaDB", e)

        finally:
            # Close database connection
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
                logging.debug("MariaDB connection is closed")

    def show_scores(self):
        records = []
        try:
            # Establish a connection to the database
            connection = mysql.connector.connect(**DB_CONFIG)
            if connection.is_connected():
                cursor = connection.cursor()
                cursor.execute(f"SELECT (nickname, score) FROM players ORDER BY score DESC LIMIT 10;")
                records = cursor.fetchall()

        except mysql.connector.Error as e:
            logging.error("Error while connecting to MariaDB", e)

        finally:
            # Close database connection
            if 'connection' in locals() and connection.is_connected():
                cursor.close()
                connection.close()
                logging.debug("MariaDB connection is closed")
        
        logging.debug(records)
            
        message = "\n"
        for i in records:
            message += f"| {i[0]}\t| {i[1]}\t|\n"
        self.wfile.write(message.encode())

    # Method to handle incoming requests
    def handle(self):
        self.score = 0
        # Prompt for and retrieve the user's nickname
        if not self.retrieve_nickname():
            self.wfile.write(b"Please provide a username\n")
            self.nickname = "guest"
        # Prompt for and select the trivia category
        self.select_category()
        if not hasattr(self, 'category'):
            return
        self.wfile.write(f"Selected category: {self.category}\n".encode())
        # Prompt for and select the trivia difficulty level
        self.select_level()
        if not hasattr(self, 'level'):
            return
        self.wfile.write(f"Selected level: {self.level}\n".encode())
        # Prompt for and select the number of questions
        self.select_amount()
        if not hasattr(self, 'amount'):
            return
        # Retrieve trivia questions from the API
        while not hasattr(self, 'questions'):
            self.retrieve_questions()
        # Display and handle each trivia question
        for question in self.questions:
            self.display_question(question)
        if self.nickname != "guest" and self.score != 0:
            self.update_scores()
        self.show_scores()
        self.wfile.write(b"Ending game\nBye\n")
        self.request.close()

def setup_db():
    try:
        # Establish a connection to the database
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS players(\
                    id INT PRIMARY KEY AUTO_INCREMENT,\
                    nickname TEXT NOT NULL,\
                    score INT NOT NULL\
                    );')
            connection.commit()

    except mysql.connector.Error as e:
        logging.error("Error while connecting to MariaDB", e)

    finally:
        # Close database connection
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            logging.debug("MariaDB connection is closed")

# Entry point of the program
if __name__ == "__main__":
    setup_db()
    # Create a TriviaServer instance and start serving requests
    server = TriviaServer(("", 2000), TriviaHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        # Shutdown the server gracefully on KeyboardInterrupt
        server.shutdown()