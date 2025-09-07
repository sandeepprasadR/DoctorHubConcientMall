import csv
import os
import requests
from io import StringIO

class DoctorSearchApp:
    def __init__(self, use_github=False):
        """
        Initialize the app with GitHub or local file support
        use_github=True: Fetches data from your GitHub repository
        use_github=False: Uses local CSV file for development
        """
        self.use_github = use_github
        if use_github:
            # Your GitHub repository URL for the CSV file
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
            print(f"Error loading from GitHub: {e}")
            return []
        except Exception as e:
            print(f"Error parsing CSV from GitHub: {e}")
            return []
    
    def load_doctors_from_local(self):
        """Load doctors data from local CSV file"""
        doctors = []
        if not os.path.exists(self.csv_path):
            return doctors
        try:
            with open(self.csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    doctors.append(row)
            return doctors
        except Exception as e:
            print(f"Error loading from local file: {e}")
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
    
    def add_doctor_local(self, details):
        """Add a new doctor to local CSV file (only works in local mode)"""
        if self.use_github:
            return {"success": False, "message": "Cannot add doctor when using GitHub mode. Switch to local mode."}
        
        try:
            # Validate required fields
            required_fields = ["Doctor Name", "Specialization", "Clinic/Location", "OPD Days", "Timings", "Contact"]
            if not all(field in details for field in required_fields):
                return {"success": False, "message": "Missing required fields"}
            
            # Check if file exists and needs header
            add_header = not os.path.exists(self.csv_path) or os.stat(self.csv_path).st_size == 0
            
            with open(self.csv_path, 'a', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=required_fields)
                if add_header:
                    writer.writeheader()
                writer.writerow(details)
            
            return {"success": True, "message": "Doctor added successfully"}
        except Exception as e:
            return {"success": False, "message": f"Error adding doctor: {str(e)}"}
    
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
            "id": hash(doctor['Doctor Name'] + doctor['Specialization']),  # Simple ID generation
            "name": doctor['Doctor Name'],
            "specialization": doctor['Specialization'],
            "clinic": doctor['Clinic/Location'],
            "days": doctor['OPD Days'],
            "timings": doctor['Timings'],
            "contact": doctor['Contact'].split(';') if ';' in doctor['Contact'] else [doctor['Contact']],
            "available": bool(doctor['OPD Days'].strip())
        }

# Flask API endpoints for mobile app (example)
def create_flask_api():
    """
    Example Flask API that your mobile app can call
    You would run this as a separate service
    """
    from flask import Flask, jsonify, request
    
    app_flask = Flask(__name__)
    doctor_app = DoctorSearchApp(use_github=True)  # Use GitHub for production
    
    @app_flask.route('/api/doctors', methods=['GET'])
    def get_all_doctors():
        doctors = doctor_app.load_doctors()
        formatted_doctors = [doctor_app.format_doctor_for_mobile(doc) for doc in doctors]
        return jsonify({"doctors": formatted_doctors, "count": len(formatted_doctors)})
    
    @app_flask.route('/api/search', methods=['GET'])
    def search_doctors():
        keyword = request.args.get('q', '').strip()
        doctors = doctor_app.load_doctors()
        results = doctor_app.search_doctors(doctors, keyword)
        formatted_results = [doctor_app.format_doctor_for_mobile(doc) for doc in results]
        return jsonify({"results": formatted_results, "count": len(formatted_results)})
    
    @app_flask.route('/api/autocomplete', methods=['GET'])
    def autocomplete():
        keyword = request.args.get('q', '').strip()
        doctors = doctor_app.load_doctors()
        suggestions = doctor_app.autocomplete_doctors(doctors, keyword)
        return jsonify({"suggestions": suggestions})
    
    @app_flask.route('/api/specializations', methods=['GET'])
    def get_specializations():
        doctors = doctor_app.load_doctors()
        specializations = list(set([doc['Specialization'] for doc in doctors if doc['Specialization']]))
        return jsonify({"specializations": sorted(specializations)})
    
    return app_flask

# Usage examples for testing
if __name__ == "__main__":
    # Example usage
    app = DoctorSearchApp(use_github=False)  # Set to True to use GitHub
    
    # Load and test
    doctors = app.load_doctors()
    print(f"Loaded {len(doctors)} doctors")
    
    # Search example
    results = app.search_doctors(doctors, "cardio")
    print(f"Found {len(results)} results for 'cardio'")
    
    # Autocomplete example
    suggestions = app.autocomplete_doctors(doctors, "dr")
    print(f"Autocomplete suggestions: {suggestions[:5]}")  # First 5
