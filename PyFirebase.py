from random import randint
import pandas as pd
from faker import Faker
from faker_e164.providers import E164Provider
from firebase_admin import auth
from google.cloud import firestore
from tabulate import tabulate

Faker.seed(0)
fake = Faker("fr_CA")
fake.add_provider(E164Provider)


def display_and_save_object(objs, filename):
    """
    :param objs: a list of objects to be displayed
    :param filename: the name of the file to save the data to
    """
    df = pd.DataFrame()

    for obj in objs:
        df = df.append(obj.to_dict(), ignore_index=True)

    print(tabulate(df, headers="keys", tablefmt="psql") + "\r\n")

    df.to_csv(filename, sep="\t", encoding="utf-8", index=False)


# The AuthUser class is a simple class that represents a firebase user.
class AuthUser:

    def __init__(self, email="", email_verified=False, phone_number="", password="", display_name="", photo_url="",
                 disabled=False):
        self.email = email
        self.email_verified = email_verified
        self.phone_number = phone_number
        self.password = password
        self.display_name = display_name
        self.photo_url = photo_url
        self.disabled = disabled

    def to_dict(self):
        """
        :return: A dictionary with the following keys:
            email: The user's email address.
            email_verified: True if the user's email has been verified, False if it hasn't.
            phone_number: The user's phone number in E.164 format.
            password: The user's password
        """
        return {
            "email": self.email,
            "email_verified": self.email_verified,
            "phone_number": self.phone_number,
            "password": self.password,
            "display_name": self.display_name,
            "photo_url": self.photo_url,
            "disabled": self.disabled,
        }


# The FirestoreUser class is a simple class that represents a user in the database. It has a Uid,
# FirstName, LastName, Xp, Achievements attributes. The Uid is the unique identifier
# for the user, and the other attributes are the user's name, xp, achievements, and past results.
#
# The FirestoreUser class has two methods: from_dict and to_dict. The from_dict method takes a
# dictionary as an argument and sets the attributes of the FirestoreUser object to the values in the
# dictionary. The to_dict method
class FirestoreUser:

    def __init__(self, uid="", firstname="", lastname="", xp=0, achievements=None):
        """
        :param uid: The unique identifier for the user
        :param firstname: The first name of the user
        :param lastname: The last name of the user
        :param xp: The amount of xp the player has, defaults to 0 (optional)
        :param achievements: a list of strings, each string is an achievement
        """
        if achievements is None:
            achievements = []

        self.Uid = uid
        self.FirstName = firstname
        self.LastName = lastname
        self.Xp = xp
        self.Achievements = achievements

    def from_dict(self, source):
        """
        The function takes in a dictionary and returns a Player object.

        :param source: The dictionary that contains the data to be converted
        """
        self.Uid = source["Uid"]
        self.FirstName = source["FirstName"]
        self.LastName = source["LastName"]
        self.Xp = source["Xp"]

        if "AchievementsList" in source:
            self.Achievements = source["AchievementsList"]
        else:
            self.Achievements = []

    def to_dict(self):
        """
        This function returns a dictionary of the user's attributes.
        :return: A dictionary with the following keys:
            "Uid": The user's unique ID
            "FirstName": The user's first name
            "LastName": The user's last name
            "Xp": The user's current XP
            "Achievements": The user's current achievements
        """
        return {
            "Uid": self.Uid,
            "FirstName": self.FirstName,
            "LastName": self.LastName,
            "Xp": self.Xp,
            "Achievements": self.Achievements
        }


# The FirestoreCompany class is a class that represents a company in the Firestore database.
#
# The class has three attributes:
# Uid: A unique identifier for the company.
# Name: The name of the company.
# Users: A list of users that work for the company.

# The class has two methods:
# to_dict: This method returns a dictionary representation of the class.
# set_uid: This method sets the Uid attribute of the class.
class FirestoreCompany:

    def __init__(self, name, users=None):
        """
        :param name: The name of the group
        :param users: a list of users in the group
        """
        if users is None:
            users = []

        self.Uid = ""
        self.Name = name
        self.Users = users

    def to_dict(self):
        """
        :return: A dictionary of all the users in the database.
        """
        return {"Uid": self.Uid, "Name": self.Name, "Users": self.Users}

    def set_uid(self, uid):
        """
        :param uid: The unique ID of the user
        """
        self.Uid = uid


# The FirebaseAuth class is responsible for creating fake users for the Auth service.
class FirebaseAuth:

    def __init__(self):
        self.users = []

    @staticmethod
    def print_all_users():
        """
        Prints all users in the auth database.
        """
        lst = []

        print("Existing users in auth:")

        for user in auth.list_users().iterate_all():
            lst.append({"display_name": user.display_name, "uid": user.uid})

        print(tabulate(lst, headers="keys", tablefmt="psql"))

    def generate_auth_users(self, number):
        """
        Generate a list of users with random names and emails.

        :param number: The number of users to create
        """
        if len(list(auth.list_users().iterate_all())) <= 1:
            self.__create_fake_auth_users(number)
            self.__create_user()

            print("\nCreated Auth Users:")
            display_and_save_object(self.users, "auth_users.csv")
        else:
            print("Auth already seeded")
            self.print_all_users()

    def __create_fake_auth_users(self, number):
        """
        Create a list of fake AuthUser objects.
        :param number: The number of users to create
        """
        for _ in range(number):
            self.users.append(
                AuthUser(
                    fake.email(),
                    fake.boolean(chance_of_getting_true=50),
                    fake.e164(region_code="CA"),
                    fake.password(),
                    fake.name(),
                    fake.image_url(),
                    fake.boolean(chance_of_getting_true=25),
                )
            )

    def __create_user(self):
        """
        Create a user for each user in the users list.
        """
        for user in self.users:
            auth.create_user(
                email=user.email,
                email_verified=user.email_verified,
                phone_number=user.phone_number,
                password=user.password,
                display_name=user.display_name,
                photo_url=user.photo_url,
                disabled=user.disabled,
            )


# The FirebaseFirestore class is a wrapper around the Firestore API. It is used to generate and store data in
# the Firestore database.
#
# The Firestore class has two methods: generate_firestore_data and print_all_companies. The
# generate_firestore_data method is used to generate data and store it in the Firestore database. The
# print_all_companies method is used to print all the companies in the Firestore database.
#
# The generate_firestore_data method has two parameters: company_number and user_number. The
# company_number
class FirebaseFirestore:

    def __init__(self):
        self.db = None
        self.companies = []
        self.users = []

        try:
            self.db = firestore.Client()
        except Exception as ex:
            print(f"Firestore exception occurred: {ex}")

    def generate_firestore_data(self, company_quantity):
        """
        :param company_quantity: The number of companies to generate
        """
        if len(self.db.collection(u"Companies").get()) <= 0:
            self.__generate_firestore_companies(company_quantity)
            self.__create_firestore_companies()
            print("\nCreated Firestore Companies:")
            display_and_save_object(self.companies, 'firestore_companies.csv')
        else:
            print("\nCompanies already seeded")
            self.print_all_companies()

        if (len(self.db.collection(u"Users").get())) <= 0:
            self.__generate_firestore_users()
            self.__create_firestore_user()
            print("\nCreated Firestore Users:")
            display_and_save_object(self.users, 'firestore_users.csv')
            self.__assign_users_to_company()
        else:
            print("\nUsers already seeded")
            self.print_all_users()

    def print_all_companies(self):
        """
        Prints all the companies in the Firestore database.
        """
        lst = []

        print("Existing companies in Firestore Companies:")

        for company in self.db.collection(u"Companies").stream():
            lst.append({"Name": company.get('Name'), "Uid": company.get('Uid')})

        print(tabulate(lst, headers="keys", tablefmt="psql"))

    def print_all_users(self):
        """
        Prints all users in the Firestore Users collection.
        """
        lst = []

        print("Existing users in Firestore Users:")

        for user in self.db.collection(u"Users").stream():
            lst.append({"Name": f"{user.get('FirstName')} {user.get('LastName')}", "Uid": user.get("Uid")})

        print(tabulate(lst, headers="keys", tablefmt="psql"))

    def __generate_firestore_companies(self, number):
        """
        :param number: The number of companies to generate
        """
        for _ in range(number):
            self.companies.append(FirestoreCompany(fake.company()))

    def __generate_firestore_users(self):
        """
        For each user in the Firestore database, create a FirestoreUser object and add it to the users list.
        """
        for user in auth.list_users().iterate_all():
            name_split = ["", ""]

            if user.display_name is not None:
                name_split = str.split(user.display_name)

            self.users.append(FirestoreUser(user.uid, name_split[0], name_split[1], fake.random_int(), []))

    def __create_firestore_user(self):
        """
        Create a Firestore document for each user in the users list.
        """
        if self.db is not None:
            for user in self.users:
                doc_ref = self.db.collection("Users").document(user.Uid)
                doc = doc_ref.get()

                if doc.exists:
                    doc_ref.update(user.to_dict())
                else:
                    doc_ref.set(user.to_dict())

    def __create_firestore_companies(self):
        """
        Create a new company in Firestore and return the new company's uid.
        """
        if self.db is not None:
            for company in self.companies:
                new_company_ref = self.db.collection("Companies").document()
                company.Uid = new_company_ref.id
                new_company_ref.set(company.to_dict())

    def __assign_users_to_company(self):
        """
        Assign users to companies.
        """
        if self.db is not None:
            tmp_users = auth.list_users().users
            docs = self.db.collection(u"Companies").stream()

            for doc in docs:
                company_users = []
                company_ref = self.db.collection(u"Companies").document(doc.id)

                for _ in range(randint(0, int(len(tmp_users) / 2))):
                    company_users.append({"company": doc.get(u"Name"), "user uid": tmp_users[-1].uid})
                    company_ref.update({"Users": firestore.ArrayUnion([tmp_users.pop().uid])})

                if tmp_users:
                    print("\nUsers added to company:")
                    print(tabulate(company_users, headers="keys", tablefmt="psql"))
