import csv
import requests
from io import StringIO
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DoctorSearchApp:
    def __init__(self, use_github=True):
        self.use_github = use_github
        if use_github:
            self.csv_url = "https://raw.githubusercontent.com/sandeepprasadR/DoctorHubConcientMall/main/doctors_data.csv"
        else:
            self.csv_path = "./doctors_data.csv"

    def clean_header(self, header):
        # Clean header keys to remove BOM or invisible chars
        return header.strip().replace('\ufeff', '')

    def load_doctors_from_github(self):
        try:
            response = requests.get(self.csv_url)
            response.raise_for_status()
            csv_content = StringIO(response.text)
            reader = csv.DictReader(csv_content)
            # Clean headers
            reader.fieldnames = [self.clean_header(h) for h in reader.fieldnames]
            doctors = []
            for row in reader:
                # Clean keys for each row
                cleaned_row = {self.clean_header(k): v.strip() for k, v in row.items()}
                doctors.append(cleaned_row)
            logger.debug(f"Loaded {len(doctors)} doctors from GitHub")
            return doctors
        except Exception as e:
            logger.error(f"Error loading from GitHub: {e}")
            return []

    def load_doctors_from_local(self):
        doctors = []
        try:
            with open(self.csv_path, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                reader.fieldnames = [self.clean_header(h) for h in reader.fieldnames]
                for row in reader:
                    cleaned_row = {self.clean_header(k): v.strip() for k, v in row.items()}
                    doctors.append(cleaned_row)
            logger.debug(f"Loaded {len(doctors)} doctors from local file")
            return doctors
        except Exception as e:
            logger.error(f"Error loading from local file: {e}")
            return []

    def load_doctors(self):
        return self.load_doctors_from_github() if self.use_github else self.load_doctors_from_local()

    # Other methods unchanged ...
    # Make sure 'Doctor Name' key use matches cleaned header
