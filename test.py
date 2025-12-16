import sys
import os
import unittest
from colorama import Fore

# Add parent directory so we can import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

class EmployeeAPITest(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        # Login to get JWT token
        res = self.client.post('/login', json={"username": "admin", "password": "password"})
        self.assertEqual(res.status_code, 200)
        token = res.get_json()['access_token']
        self.headers = {'Authorization': f'Bearer {token}'}

    def test_unauthorized(self):
        res = self.client.get('/employees')
        self.assertEqual(res.status_code, 401)
        print(Fore.GREEN + "Unauthorized blocked")

    def test_get_employees(self):
        res = self.client.get('/employees', headers=self.headers)
        self.assertEqual(res.status_code, 200)
        print(Fore.GREEN + "GET employees passed")

    def test_search(self):
        res = self.client.get('/employees/search?role=Engineer', headers=self.headers)
        self.assertEqual(res.status_code, 200)
        print(Fore.GREEN + "Search passed")

    def test_create_employee(self):
        res = self.client.post('/employees', headers=self.headers, json={
            "first_name": "Test",
            "last_name": "User",
            "email": "testuser@example.com",
            "role": "Tester",
            "salary": 50000
        })
        self.assertEqual(res.status_code, 201)
        print(Fore.GREEN + "Create passed")

    def test_update_employee(self):
        res = self.client.put('/employees/1', headers=self.headers, json={
            "role": "Updated Role",
            "salary": 60000
        })
        self.assertEqual(res.status_code, 200)
        print(Fore.GREEN + "Update passed")

    def test_delete_employee(self):
        res = self.client.delete('/employees/20', headers=self.headers)
        self.assertIn(res.status_code, [200, 404])
        print(Fore.GREEN + "Delete passed")

if __name__ == '__main__':
    unittest.main()
