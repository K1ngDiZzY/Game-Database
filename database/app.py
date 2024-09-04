from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)


def get_player_count(app_id):
    url = f'https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={app_id}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['response']['player_count']
    logging.warning(f"Failed to get player count for app_id: {app_id}")
    return 0


app = Flask(__name__)


# Initialize the SQLite database
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS games (
            id INTEGER PRIMARY KEY,
            game_name TEXT NOT NULL,
            app_id INTEGER NOT NULL,
            release_date TEXT NOT NULL,
            active_players INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


init_db()


@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM games')
    games = cursor.fetchall()

    # Update the active players count for each game
    for game in games:
        app_id = game[2]
        player_count = get_player_count(app_id)
        if player_count == 0:
            logging.warning(f"Game '{game[1]}' (app_id: {app_id}) did not update player count.")
        cursor.execute('UPDATE games SET active_players = ? WHERE id = ?', (player_count, game[0]))

    conn.commit()
    conn.close()

    # Reload the updated data
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM games')
    games = cursor.fetchall()
    conn.close()

    return render_template('index.html', games=games)


@app.route('/add', methods=['GET', 'POST'])
def add_game():
    if request.method == 'POST':
        game_name = request.form['game_name']
        app_id = request.form['app_id']
        release_date = request.form['release_date']

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO games (game_name, app_id, release_date, active_players) VALUES (?, ?, ?, ?)',
                       (game_name, app_id, release_date, 0))  # Initial active_players set to 0
        conn.commit()
        conn.close()
        return redirect(url_for('index'))

    return render_template('add_game.html')


if __name__ == '__main__':
    app.run(debug=True)
