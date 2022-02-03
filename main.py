import json
import os
from os import path
import firebase_admin
from PyFirebase import FirebaseAuth, FirebaseFirestore

config_file = "config.json"

# Initialize the Firebase Admin SDK, and generate the auth users and companies.
if __name__ == '__main__':

    if path.isfile(config_file):
        quantities = {}

        print("Firebase environment variables:")
        # Load the configuration file.
        with open(config_file) as json_file:
            data = json.load(json_file)

            # Set the environment variables.
            for key, value in data['environment'].items():
                print(f"os.environ[{key}] = {value}")
                os.environ[key] = value

            print("\nQuantities:")
            # Set the quantities.
            for key, value in data["quantities"].items():
                print(f"quantities[{key}] = {value}")
                quantities[key] = value

        print("")

        if os.environ["GOOGLE_APPLICATION_CREDENTIALS"] and os.environ["GCLOUD_PROJECT"]:
            # initialize firebase application
            firebase_admin.initialize_app()

            # Generate a set number of auth users
            auth = FirebaseAuth()
            auth.generate_auth_users(quantities["users"])

            # Generating a set number of companies and associate auth users
            firestore = FirebaseFirestore()
            firestore.generate_firestore_data(quantities["companies"])
        else:
            print(f"Environment variables not set in {config_file}")
    else:
        print(f"Missing config file {config_file}")

    input("\nPress Enter to continue...")
