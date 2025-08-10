from flask import Flask, render_template, request, redirect, url_for, send_file
import sqlite3, csv, io
import os

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB = os.path.join(BASE_DIR, 'dlmtc_lcs.db')

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@app.route('/')
def index():
    return redirect(url_for('session_list'))

@app.route('/session/new', methods=['GET', 'POST'])
def new_session():
    if request.method == 'POST':
        data = request.form
        db = get_db()
        cursor = db.execute('''
            INSERT INTO session (date, project, frequency, month, location, attended_by, verified_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data['date'], data['project'], data['frequency'], data['month'], data['location'], data['attended_by'], data['verified_by']))
        db.commit()
        return redirect(url_for('add_items', session_id=cursor.lastrowid))
    return render_template('session_form.html')

@app.route('/sessions')
def session_list():
    db = get_db()
    sessions = db.execute('SELECT * FROM session ORDER BY created_at DESC').fetchall()
    return render_template('session_list.html', sessions=sessions)

@app.route('/session/<int:session_id>/edit', methods=['GET', 'POST'])
def edit_session(session_id):
    db = get_db()
    session = db.execute('SELECT * FROM session WHERE id=?', (session_id,)).fetchone()
    if not session:
        return "Session not found", 404
    if request.method == 'POST':
        data = request.form
        db.execute('''
            UPDATE session SET date=?, project=?, frequency=?, month=?,
            location=?, attended_by=?, verified_by=? WHERE id=?
        ''', (data['date'], data['project'], data['frequency'], data['month'],
              data['location'], data['attended_by'], data['verified_by'], session_id))
        db.commit()
        return redirect(url_for('session_list'))
    return render_template('edit_session.html', session=session)

@app.route('/session/<int:session_id>/delete')
def delete_session(session_id):
    db = get_db()
    db.execute('DELETE FROM checklist_item WHERE session_id=?', (session_id,))
    db.execute('DELETE FROM session WHERE id=?', (session_id,))
    db.commit()
    return redirect(url_for('session_list'))

@app.route('/session/<int:session_id>/duplicate')
def duplicate_session(session_id):
    db = get_db()
    old_session = db.execute('SELECT * FROM session WHERE id=?', (session_id,)).fetchone()
    if not old_session:
        return "Original session not found", 404

    # Create duplicated session
    cursor = db.execute('''
        INSERT INTO session (date, project, frequency, month, location, attended_by, verified_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (old_session['date'], old_session['project'], old_session['frequency'],
          old_session['month'], old_session['location'], old_session['attended_by'],
          old_session['verified_by']))
    new_session_id = cursor.lastrowid

    # Duplicate checklist items
    items = db.execute('SELECT * FROM checklist_item WHERE session_id=?', (session_id,)).fetchall()
    for item in items:
        db.execute('''
            INSERT INTO checklist_item (session_id, item_no, panel_ref, asset_code,
            item_description, values_observation, any_abnormality, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (new_session_id, item['item_no'], item['panel_ref'], item['asset_code'],
              item['item_description'], item['values_observation'], item['any_abnormality'],
              item['remarks']))
    db.commit()
    return redirect(url_for('add_items', session_id=new_session_id))

@app.route('/session/<int:session_id>/items', methods=['GET', 'POST'])
def add_items(session_id):
    db = get_db()
    session = db.execute('SELECT * FROM session WHERE id=?', (session_id,)).fetchone()
    if not session:
        return "Session not found", 404

    if request.method == 'POST':
        data = request.form
        db.execute('''
            INSERT INTO checklist_item (session_id, item_no, panel_ref, asset_code,
            item_description, values_observation, any_abnormality, remarks)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session_id, data.get('item_no'), data.get('panel_ref'), data.get('asset_code'),
              data['item_description'], data.get('values_observation'),
              data.get('any_abnormality'), data.get('remarks')))
        db.commit()
        return redirect(url_for('add_items', session_id=session_id))

    items = db.execute('SELECT * FROM checklist_item WHERE session_id=?', (session_id,)).fetchall()
    return render_template('items_form.html', session=session, items=items)

@app.route('/item/<int:item_id>/edit', methods=['GET', 'POST'])
def edit_item(item_id):
    db = get_db()
    item = db.execute('SELECT * FROM checklist_item WHERE id=?', (item_id,)).fetchone()
    if not item:
        return "Item not found", 404

    if request.method == 'POST':
        data = request.form
        db.execute('''
            UPDATE checklist_item SET item_no=?, panel_ref=?, asset_code=?, item_description=?,
            values_observation=?, any_abnormality=?, remarks=? WHERE id=?
        ''', (data.get('item_no'), data.get('panel_ref'), data.get('asset_code'),
              data['item_description'], data.get('values_observation'),
              data.get('any_abnormality'), data.get('remarks'), item_id))
        db.commit()
        return redirect(url_for('add_items', session_id=item['session_id']))

    return render_template('edit_item.html', item=item)

@app.route('/item/<int:item_id>/delete')
def delete_item(item_id):
    db = get_db()
    item = db.execute('SELECT * FROM checklist_item WHERE id=?', (item_id,)).fetchone()
    if not item:
        return "Item not found", 404
    session_id = item['session_id']
    db.execute('DELETE FROM checklist_item WHERE id=?', (item_id,))
    db.commit()
    return redirect(url_for('add_items', session_id=session_id))

@app.route('/session/<int:session_id>/export')
def export_csv(session_id):
    db = get_db()
    session = db.execute('SELECT * FROM session WHERE id=?', (session_id,)).fetchone()
    if not session:
        return "Session not found", 404
    items = db.execute('SELECT * FROM checklist_item WHERE session_id=?', (session_id,)).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Date', 'Project', 'Frequency', 'Month', 'Location',
        'Attended By', 'Verified By',
        'Item No', 'Panel Ref', 'Asset Code', 'Item Description',
        'Values / Observation', 'Any Abnormality', 'Remarks'
    ])
    for item in items:
        writer.writerow([
            session['date'], session['project'], session['frequency'], session['month'], session['location'],
            session['attended_by'], session['verified_by'],
            item['item_no'], item['panel_ref'], item['asset_code'], item['item_description'],
            item['values_observation'], item['any_abnormality'], item['remarks']
        ])
    output.seek(0)
    return send_file(io.BytesIO(output.getvalue().encode()), mimetype='text/csv', as_attachment=True,
                     download_name=f'checklist_session_{session_id}.csv')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
