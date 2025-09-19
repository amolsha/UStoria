from flask import Blueprint, render_template, jsonify
import sqlite3

from . import dashboard_bp

DB_PATH = "data/evaluations.db"


def get_aggregated_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Count pass/fail per criterion
    cursor.execute("""
        SELECT criterion, 
               SUM(CASE WHEN passed = 1 THEN 1 ELSE 0 END) as passed_count,
               SUM(CASE WHEN passed = 0 THEN 1 ELSE 0 END) as failed_count
        FROM evaluations
        GROUP BY criterion
    """)
    data = cursor.fetchall()
    conn.close()

    # Convert to dict
    result = {
        "criteria": [],
        "passed": [],
        "failed": []
    }
    for row in data:
        result["criteria"].append(row[0])
        result["passed"].append(row[1])
        result["failed"].append(row[2])
    return result


@dashboard_bp.route("/", methods=["GET"])
def show_dashboard():
    return render_template("dashboard.html")


@dashboard_bp.route("/data")
def dashboard_data():
    data = get_aggregated_data()
    return jsonify(data)
