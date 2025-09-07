
"""
Doctor API Server for DoctorHub Conscient Mall
Flask REST API server for mobile app integration
Supports search, autocomplete, and data management for doctors
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import csv
import os
import requests
from io import StringIO
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DoctorSearchApp:
    def __init__(self, use_github=True):
        """
        Initialize the app with GitHub or local file support
        use_github=True: Fetches data from GitHub repository (recommended for production)
        use_github=False: Uses local CSV file for development
        """
        self.use_github = use_github
        if use_github:
            # GitHub repository URL for the CSV file
            self.csv_url = "https://raw.githubusercontent.com/sandeepprasadR/DoctorHubConcientMall/main/doctors_data.csv"
        else:
            # Local development path
            self.csv_path = './doctors_data.csv'

    def load_doctors_from_github(self):
        """Load doctors data directly from GitHub repository"""
        try:
            response = requests.get(self.csv_url)
            response.raise_for_status()
            csv_content = StringIO(response.text)
            reader = csv.DictReader(csv_content)
            return list(reader)
        except requests.RequestException as e:
            logger.error(f"Error loading from GitHub: {e}")
            return []
        except Exception as e:
            logger.error(f"Error parsing CSV from GitHub: {e}")
            return []

    def load_doctors_from_local(self):
        """Load doctors data from local CSV file"""
        doctors = []
        if not os.path.exists(self.csv_path):
            logger.warning(f"Local CSV file not found: {self.csv_path}")
            return doctors
        try:
            with open(self.csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    doctors.append(row)
            return doctors
        except Exception as e:
            logger.error(f"Error loading from local file: {e}")
            return []

    def load_doctors(self):
        """Load doctors data based on configuration"""
        if self.use_github:
            return self.load_doctors_from_github()
        else:
            return self.load_doctors_from_local()

    def autocomplete_doctors(self, doctors, keyword):
        """
        Returns unique autocomplete suggestions for name and specialization fields
        Perfect for mobile app type-ahead functionality
        """
        keyword = keyword.lower().strip()
        if not keyword:
            return []

        suggestions = set()
        for doc in doctors:
            # Check doctor names
            if keyword in doc['Doctor Name'].lower():
                suggestions.add(doc['Doctor Name'])
            # Check specializations
            if keyword in doc['Specialization'].lower():
                suggestions.add(doc['Specialization'])
            # Check clinic names
            if keyword in doc['Clinic/Location'].lower():
                suggestions.add(doc['Clinic/Location'])

        return sorted(list(suggestions))

    def search_doctors(self, doctors, keyword):
        """
        Returns doctor records matching the keyword in any field
        Supports partial matching across all fields
        """
        keyword = keyword.lower().strip()
        if not keyword:
            return doctors  # Return all if no keyword

        results = []
        for doc in doctors:
            if (keyword in doc['Doctor Name'].lower() or 
                keyword in doc['Specialization'].lower() or
                keyword in doc['Clinic/Location'].lower() or
                keyword in doc['OPD Days'].lower() or
                keyword in doc['Timings'].lower() or
                keyword in doc['Contact'].lower()):
                results.append(doc)
        return results

    def search_by_specialization(self, doctors, specialization):
        """Search specifically by specialization"""
        specialization = specialization.lower().strip()
        return [doc for doc in doctors if specialization in doc['Specialization'].lower()]

    def search_by_name(self, doctors, name):
        """Search specifically by doctor name"""
        name = name.lower().strip()
        return [doc for doc in doctors if name in doc['Doctor Name'].lower()]

    def get_doctors_by_availability(self, doctors, day):
        """Filter doctors by availability day"""
        day = day.lower().strip()
        available_doctors = []
        for doc in doctors:
            if day in doc['OPD Days'].lower():
                available_doctors.append(doc)
        return available_doctors

    def format_doctor_for_mobile(self, doctor):
        """Format doctor data for mobile app consumption"""
        return {
            "id": hash(doctor['Doctor Name'] + doctor['Specialization']),
            "name": doctor['Doctor Name'],
            "specialization": doctor['Specialization'],
            "clinic": doctor['Clinic/Location'],
            "days": doctor['OPD Days'],
            "timings": doctor['Timings'],
            "contact": doctor['Contact'].split(';') if ';' in doctor['Contact'] else [doctor['Contact']],
            "available": bool(doctor['OPD Days'].strip())
        }

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for mobile app access

# Initialize doctor search app (use GitHub for production)
doctor_app = DoctorSearchApp(use_github=True)

# API Documentation HTML template
API_DOC_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Doctor Hub API Documentation</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .method { background: #007bff; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; }
        .url { font-family: monospace; background: #e9ecef; padding: 2px 5px; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Doctor Hub Conscient Mall - API Documentation</h1>
    <p>REST API for searching doctors and clinics in Conscient One Mall, Sector 109, Gurugram</p>

    <div class="endpoint">
        <h3><span class="method">GET</span> <span class="url">/api/doctors</span></h3>
        <p>Get all doctors in the system</p>
        <p><strong>Response:</strong> JSON array of all doctors with formatted data</p>
    </div>

    <div class="endpoint">
        <h3><span class="method">GET</span> <span class="url">/api/search</span></h3>
        <p>Search doctors by keyword</p>
        <p><strong>Parameters:</strong> <code>q</code> - search keyword</p>
        <p><strong>Example:</strong> <code>/api/search?q=cardiology</code></p>
    </div>

    <div class="endpoint">
        <h3><span class="method">GET</span> <span class="url">/api/autocomplete</span></h3>
        <p>Get autocomplete suggestions for type-ahead functionality</p>
        <p><strong>Parameters:</strong> <code>q</code> - partial keyword</p>
        <p><strong>Example:</strong> <code>/api/autocomplete?q=dr</code></p>
    </div>

    <div class="endpoint">
        <h3><span class="method">GET</span> <span class="url">/api/specializations</span></h3>
        <p>Get all unique specializations</p>
        <p><strong>Response:</strong> JSON array of specializations</p>
    </div>

    <div class="endpoint">
        <h3><span class="method">GET</span> <span class="url">/api/available</span></h3>
        <p>Get doctors available on a specific day</p>
        <p><strong>Parameters:</strong> <code>day</code> - day of the week</p>
        <p><strong>Example:</strong> <code>/api/available?day=monday</code></p>
    </div>

    <div class="endpoint">
        <h3><span class="method">GET</span> <span class="url">/api/health</span></h3>
        <p>Health check endpoint</p>
        <p><strong>Response:</strong> Server status and data count</p>
    </div>

    <h3>Sample Response Format:</h3>
    <pre>
{
  "id": 12345,
  "name": "Dr. Rajesh Kumar Dudeja",
  "specialization": "Consultant Medicine",
  "clinic": "Raj Clinic",
  "days": "Mon-Fri",
  "timings": "9:00 AM - 6:00 PM",
  "contact": ["7048950929", "9818105501"],
  "available": true
}
    </pre>

    <p><strong>Base URL:</strong> <code>{{ base_url }}</code></p>
    <p><strong>Last Updated:</strong> {{ timestamp }}</p>
</body>
</html>
"""

# API Routes

@app.route('/')
def home():
    """API Documentation homepage"""
    return render_template_string(
        API_DOC_TEMPLATE, 
        base_url=request.base_url,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        doctors = doctor_app.load_doctors()
        return jsonify({
            "status": "healthy",
            "message": "Doctor Hub API is running",
            "data_source": "GitHub" if doctor_app.use_github else "Local",
            "total_doctors": len(doctors),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/doctors')
def get_all_doctors():
    """Get all doctors in the system"""
    try:
        doctors = doctor_app.load_doctors()
        formatted_doctors = [doctor_app.format_doctor_for_mobile(doc) for doc in doctors]

        return jsonify({
            "success": True,
            "doctors": formatted_doctors,
            "count": len(formatted_doctors),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_all_doctors: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/search')
def search_doctors():
    """Search doctors by keyword"""
    try:
        keyword = request.args.get('q', '').strip()
        if not keyword:
            return jsonify({
                "success": False,
                "error": "Search keyword 'q' is required",
                "timestamp": datetime.now().isoformat()
            }), 400

        doctors = doctor_app.load_doctors()
        results = doctor_app.search_doctors(doctors, keyword)
        formatted_results = [doctor_app.format_doctor_for_mobile(doc) for doc in results]

        return jsonify({
            "success": True,
            "query": keyword,
            "results": formatted_results,
            "count": len(formatted_results),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in search_doctors: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/autocomplete')
def autocomplete():
    """Get autocomplete suggestions for type-ahead functionality"""
    try:
        keyword = request.args.get('q', '').strip()
        if not keyword:
            return jsonify({
                "success": False,
                "error": "Search keyword 'q' is required",
                "timestamp": datetime.now().isoformat()
            }), 400

        doctors = doctor_app.load_doctors()
        suggestions = doctor_app.autocomplete_doctors(doctors, keyword)

        return jsonify({
            "success": True,
            "query": keyword,
            "suggestions": suggestions,
            "count": len(suggestions),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in autocomplete: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/specializations')
def get_specializations():
    """Get all unique specializations"""
    try:
        doctors = doctor_app.load_doctors()
        specializations = list(set([
            doc['Specialization'].strip() 
            for doc in doctors 
            if doc['Specialization'].strip()
        ]))
        specializations.sort()

        return jsonify({
            "success": True,
            "specializations": specializations,
            "count": len(specializations),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_specializations: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/available')
def get_available_doctors():
    """Get doctors available on a specific day"""
    try:
        day = request.args.get('day', '').strip()
        if not day:
            return jsonify({
                "success": False,
                "error": "Day parameter is required",
                "timestamp": datetime.now().isoformat()
            }), 400

        doctors = doctor_app.load_doctors()
        available = doctor_app.get_doctors_by_availability(doctors, day)
        formatted_available = [doctor_app.format_doctor_for_mobile(doc) for doc in available]

        return jsonify({
            "success": True,
            "day": day,
            "available_doctors": formatted_available,
            "count": len(formatted_available),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_available_doctors: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/doctor/<int:doctor_id>')
def get_doctor_by_id(doctor_id):
    """Get specific doctor by ID"""
    try:
        doctors = doctor_app.load_doctors()
        formatted_doctors = [doctor_app.format_doctor_for_mobile(doc) for doc in doctors]

        # Find doctor by ID
        doctor = next((d for d in formatted_doctors if d['id'] == doctor_id), None)

        if not doctor:
            return jsonify({
                "success": False,
                "error": "Doctor not found",
                "timestamp": datetime.now().isoformat()
            }), 404

        return jsonify({
            "success": True,
            "doctor": doctor,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_doctor_by_id: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "message": "Please check the API documentation at the root URL",
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "timestamp": datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    # Configuration
    DEBUG_MODE = os.getenv('DEBUG', 'False').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')

    logger.info(f"Starting Doctor Hub API Server on {HOST}:{PORT}")
    logger.info(f"Debug mode: {DEBUG_MODE}")
    logger.info(f"Data source: {'GitHub' if doctor_app.use_github else 'Local'}")

    # Run the Flask app
    app.run(
        debug=DEBUG_MODE,
        host=HOST,
        port=PORT
    )
