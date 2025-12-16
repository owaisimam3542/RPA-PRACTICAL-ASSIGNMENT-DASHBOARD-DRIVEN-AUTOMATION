from flask import Flask, render_template, request
from automation import run_automation

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def dashboard():
    result = None
    employees = []

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        emp_id = request.form["emp_id"]

        result, employees = run_automation(
            username, password, first_name, last_name, emp_id
        )

    return render_template("index.html", result=result, employees=employees)

if __name__ == "__main__":
    app.run(debug=True)
