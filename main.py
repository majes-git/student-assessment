import gspread
import os
import secrets
import sys
from flask import Flask, render_template, request, jsonify
from jinja2 import Environment, FunctionLoader


app = Flask(__name__)

client = gspread.service_account(os.environ.get('GOOGLE_CREDENTIALS', 'credentials.json'))
spreadsheet = client.open(os.environ.get('GOOGLE_SPREADSHEET', 'Students Assessment'))


def load_secret_key():
    path = os.environ.get('FLASK_SECRET_PATH', os.path.join(os.getcwd(), 'flask_secret.key'))

    # Try to load existing key
    if os.path.exists(path):
        with open(path) as f:
            secret = f.read().strip()
            if secret:
               return secret

    # Auto-generate and save secure key
    secret = secrets.token_urlsafe(32)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(secret)
    print(f'[INFO] Generated new Flask SECRET_KEY at: {path}')
    return secret


def load_template(filename):
    # if file cannot be found (type == None) return a 404
    data = None

    # first try to load a template from program directory (templates)
    # if not possible, try to load it from the pyz
    dir = os.path.join(os.path.dirname(sys.argv[0]), 'templates')
    try:
        with open(os.path.join(dir, filename)) as fd:
            data = fd.read()
            return data
    except FileNotFoundError:
        pass

    # try to load template from pyz
    try:
        data = pkgutil.get_data('templates', filename).decode('utf8')
    except OSError:
        data = f'--> Could not find template: {filename}\n\n'
    return data


@app.route('/', methods=['GET', 'POST'])
def index():
    selected_sheet_title = None
    selected_id = None
    word_count = 300
    result_string = None
    original_name_map = {}

    sheet_titles = [ws.title for ws in spreadsheet.worksheets()]
    dropdown_entries = []

    if request.method == 'POST':
        selected_sheet_title = request.form.get('sheet')
        selected_id = request.form.get('id')
        word_count = request.form.get('word_count', '').strip()

        try:
            worksheet = spreadsheet.worksheet(selected_sheet_title)
            all_rows = worksheet.get_all_values()
            headers = all_rows[1]

            for row in all_rows[2:]:
                if row and row[0] == selected_id:
                    original_first_name = row[1]
                    original_last_name = row[2]
                    gender = row[3].strip().lower() if len(row) > 3 else ''
                    # Replace name based on gender and for frontend transformation
                    display_name = f'{original_first_name} {original_last_name}'
                    if gender:
                        if gender == 'weiblich':
                            original_name_map = {
                                'Erika': original_first_name,
                                'Musterschülerin': original_last_name,
                            }
                        elif gender == 'männlich':
                            original_name_map = {
                                'Max': original_first_name,
                                'Musterschüler': original_last_name,
                            }
                        display_name = f'{list(original_name_map.keys())[0]} {list(original_name_map.keys())[1]}'

                    lines = [f'Name: {display_name}']
                    for i in range(4, len(headers)):
                        if i < len(row) and row[i].strip():
                            lines.append(f'{headers[i]}: {row[i]}')

                    assessment_string = '\n'.join(lines)
                    result_string = f'Bitte generiere eine Formulierte Zeugnisbeurteilung (1. Klasse, Brandenburg) für folgenden Schüler ohne Titelzeile und Schlusssatz in schulischer Sprache ({word_count} Wörter) :\n'
                    result_string += '"""' + assessment_string + '"""'
                    break

        except gspread.exceptions.WorksheetNotFound:
            result_string = 'Fehler: Arbeitsblatt nicht gefunden.'

    template = env.get_template('form.html')
    return template.render(
        sheet_titles=sheet_titles,
        selected_sheet_title=selected_sheet_title,
        entries=dropdown_entries,
        result=result_string,
        selected_id=selected_id,
        word_count=word_count,
        name_map=original_name_map,
    )

@app.route('/get_entries', methods=['POST'])
def get_entries():
    data = request.json
    sheet_title = data.get('sheet')
    try:
        worksheet = spreadsheet.worksheet(sheet_title)
        all_rows = worksheet.get_all_values()
        entries = []
        for row in all_rows[1:]:
            if len(row) >= 3 and row[0].strip():
                entries.append({
                    'id': row[0],
                    'label': f'{row[0]} - {row[1]} {row[2]}'
                })
        return jsonify(entries=entries)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    global env
    env = Environment(loader=FunctionLoader(load_template), cache_size=0)
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.secret_key = load_secret_key()
    app.run(debug=False, use_reloader=False)
