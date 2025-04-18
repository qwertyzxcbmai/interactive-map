

from flask import Flask, render_template, request, jsonify
import sqlite3
import random
import os  # os

app = Flask(__name__)
DATABASE = "markers.db"
def init_db():

    if os.path.exists(DATABASE):
        try:
            os.remove(DATABASE)
            print(f"Old database '{DATABASE}' removed.")
        except OSError as e:
            print(f"Error removing database file: {e}")

    # Создаем базу и таблицу
    try:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS markers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lat REAL NOT NULL, 
                    lon REAL NOT NULL,
                    name TEXT, 
                    description TEXT,
                    rating INTEGER 
                )
            """)
            conn.commit()
            print("Database initialized!")
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    if not os.path.exists(DATABASE):
        init_db()
    return render_template('index.html')
pip freeze > requirements.txt

@app.route('/add_marker', methods=['POST'])
def add_marker():
    data = request.json
    if not all(k in data for k in ("lat", "lon", "rating")):
        return jsonify({"status": "error", "message": "Missing required data (lat, lon, rating)"}), 400
    try:
        lat = float(data['lat'])
        lon = float(data['lon'])
        name = data.get('name', 'No name')
        description = data.get('description', '')
        rating_val = data['rating']

        rating = None
        if rating_val is not None:
            try:
                rating_float = float(rating_val)
                if 0 <= rating_float <= 10:
                    rating = round(rating_float, 1)
                else:
                    raise ValueError()
            except (ValueError, TypeError):
                return jsonify({"status": "error", "message": "Rating must be a number between 0 and 10"}), 400
        else:  #  или 0
            rating = None

    except (ValueError, TypeError, KeyError) as e:
        return jsonify({"status": "error", "message": f"Invalid data format or value: {e}"}), 400

    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO markers (lat, lon, name, description, rating) VALUES (?, ?, ?, ?, ?)",
            (lat, lon, name, description, rating)
        )
        conn.commit()
        marker_id = cursor.lastrowid
        conn.close()
        return jsonify({"status": "ok", "id": marker_id})
    except sqlite3.Error as e:
        print(f"Database error on add: {e}")
        if conn: conn.close()
        return jsonify({"status": "error", "message": "Database error"}), 500


@app.route('/get_markers')
def get_markers():
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, lat, lon, name, description, rating FROM markers")
        markers = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(markers)
    except sqlite3.Error as e:
        print(f"Database error on get: {e}")
        if conn: conn.close()
        return jsonify({"status": "error", "message": "Database error"}), 500

@app.route('/delete_marker/<int:marker_id>', methods=['DELETE'])
def delete_marker_route(marker_id):
    conn = None
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM markers WHERE id = ?", (marker_id,))
        conn.commit()
        deleted_count = cursor.rowcount
        conn.close()
        if deleted_count > 0:
            print(f"Marker {marker_id} deleted successfully.")
            return jsonify({"status": "ok", "message": f"Marker {marker_id} deleted"})
        else:
            print(f"Marker {marker_id} not found for deletion.")
            return jsonify({"status": "error", "message": f"Marker {marker_id} not found"}), 404
    except sqlite3.Error as e:
        print(f"Database error on delete: {e}")
        if conn: conn.close()
        return jsonify({"status": "error", "message": "Database error"}), 500


if __name__ == '__main__':
    init_db()
    app.run(debug=True)