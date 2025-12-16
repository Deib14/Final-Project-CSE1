import unittest
from app import app
from colorama import Fore

API_KEY = "CSE1-SECURE-KEY"

class EmployeeAPITest(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.headers = {'Authorization': API_KEY}

    def test_unauthorized(self):
        res = self.client.get('/employees')
        self.assertEqual(res.status_code, 401)
        print(Fore.GREEN + "Unauthorized blocked")

    def test_get_employees(self):
        res = self.client.get('/employees', headers=self.headers)
        self.assertEqual(res.status_code, 200)
        print(Fore.GREEN + "GET employees passed")

    def test_search(self):
        res = self.client.get('/employees/search?role=Engineer',
                              headers=self.headers)
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
