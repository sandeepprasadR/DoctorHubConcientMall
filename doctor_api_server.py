from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import logging
from datetime import datetime
from doctor_search_app import DoctorSearchApp

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app) 

doctor_app = DoctorSearchApp(use_github=True)

@app.route('/')
def home():
    return "<h1>Doctor Hub API is running</h1><p>Use /api/doctors to get doctors list.</p>"

@app.route('/api/doctors')
def get_all_doctors():
    try:
        doctors = doctor_app.load_doctors()
        logger.debug(f"Doctors data loaded: {doctors[:2]}")  # Debug first 2 entries
        formatted_doctors = []
        for doc in doctors:
            if 'Doctor Name' in doc:
                formatted_doctors.append({
                    "id": hash(doc['Doctor Name'] + doc.get('Specialization', '')),
                    "name": doc.get('Doctor Name', ''),
                    "specialization": doc.get('Specialization',''),
                    "clinic": doc.get('Clinic/Location', ''),
                    "days": doc.get('OPD Days', ''),
                    "timings": doc.get('Timings', ''),
                    "contact": doc.get('Contact','').split(';') if ';' in doc.get('Contact','') else [doc.get('Contact','')],
                    "available": bool(doc.get('OPD Days','').strip())
                })
        return jsonify({"success": True, "doctors": formatted_doctors, "count": len(formatted_doctors), "timestamp": datetime.now().isoformat()})
    except Exception as e:
        logger.error(f"Error in get_all_doctors: {e}")
        return jsonify({"success": False, "error": str(e), "timestamp": datetime.now().isoformat()}), 500

# You can add more API endpoints here following the same pattern
# Example: /api/search, /api/autocomplete, /api/health etc.

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)
