from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

tips = [
    {"id": 1, "title": "Stay Hydrated", "content": "Drink at least 8 glasses of water daily to keep your skin glowing."},
    {"id": 2, "title": "Always Use Sunscreen", "content": "Protect your skin from UV rays to prevent premature aging."}
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tips')
def tips_page():
    return render_template('tips.html', tips=tips)

@app.route('/add', methods=['GET', 'POST'])
def add_tips():
    if request.method == 'POST':
        new_id = len(tips) + 1
        title = request.form['title']
        content = request.form['content']
        tips.append({"id": new_id, "title": title, "content": content})
        return redirect(url_for('tips_page'))
    return render_template('add_tips.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_tips(id):
    tip = next((t for t in tips if t['id'] == id), None)
    if tip is None:
        return "Tip not found!", 404
    if request.method == 'POST':
        tip['title'] = request.form['title']
        tip['content'] = request.form['content']
        return redirect(url_for('tips_page'))
    return render_template('edit_tips.html', tip=tip)

@app.route('/delete/<int:id>')
def delete_tips(id):
    global tips
    tips = [t for t in tips if t['id'] != id]
    return redirect(url_for('tips_page'))

if __name__ == '__main__':
    app.run(debug=True)
