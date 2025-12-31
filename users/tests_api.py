from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class UsersAPITests(APITestCase):
    def get_token(self, username, password):
        res = self.client.post(
            "/api/token/",
            {"username": username, "password": password},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        return res.data["access"]

    def auth_as(self, username, password):
        token = self.get_token(username, password)
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)

    def make_admin(self, username="admin1", password="testpass123"):
        admin = User.objects.create_user(username=username, password=password, role="admin")
        # Por si el save() no seteó is_staff (o si role se cambia luego)
        admin.is_staff = True
        admin.save(update_fields=["is_staff"])
        return admin

    def test_register_student_creates_user_and_flags(self):
        res = self.client.post(
            "/api/users/users/register-student/",
            {"username": "stud1", "password": "testpass123", "nombre": "Juan", "apellido": "Perez"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["role"], "student")
        self.assertTrue(res.data["student_enabled"])
        self.assertFalse(res.data["instructor_enabled"])

        u = User.objects.get(username="stud1")
        # Con tu modelo “full”, el signal asegura ambos perfiles
        self.assertTrue(hasattr(u, "student_profile"))
        self.assertTrue(hasattr(u, "instructor_profile"))

    def test_register_instructor_creates_user_and_flags(self):
        res = self.client.post(
            "/api/users/users/register-instructor/",
            {"username": "inst1", "password": "testpass123", "bio": "Hola", "especialidad": "Python"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["role"], "instructor")
        self.assertTrue(res.data["instructor_enabled"])

        u = User.objects.get(username="inst1")
        self.assertTrue(hasattr(u, "student_profile"))
        self.assertTrue(hasattr(u, "instructor_profile"))

    def test_me_requires_auth(self):
        res = self.client.get("/api/users/users/me/")
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_me_returns_current_user(self):
        User.objects.create_user(username="u1", password="testpass123")
        self.auth_as("u1", "testpass123")

        res = self.client.get("/api/users/users/me/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["username"], "u1")

    def test_me_patch_updates_user(self):
        User.objects.create_user(username="u2", password="testpass123", email="[email protected]")
        self.auth_as("u2", "testpass123")

        res = self.client.patch(
            "/api/users/users/me/",
            {"first_name": "Carlos", "last_name": "Lopez"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["first_name"], "Carlos")
        self.assertEqual(res.data["last_name"], "Lopez")

    def test_change_password(self):
        User.objects.create_user(username="u3", password="testpass123")
        self.auth_as("u3", "testpass123")

        res = self.client.post(
            "/api/users/users/change-password/",
            {"old_password": "testpass123", "new_password": "newpass1234"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Debe poder obtener token con la nueva password
        token = self.get_token("u3", "newpass1234")
        self.assertTrue(token)

    def test_admin_can_enable_instructor(self):
        self.make_admin(username="admin2", password="testpass123")
        target = User.objects.create_user(username="u4", password="testpass123")
        self.auth_as("admin2", "testpass123")

        res = self.client.patch(
            f"/api/users/users/{target.id}/enable-instructor/",
            {"enabled": True},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data["instructor_enabled"])

    def test_admin_can_enable_student(self):
        self.make_admin(username="admin3", password="testpass123")
        target = User.objects.create_user(username="u5", password="testpass123", student_enabled=False)
        self.auth_as("admin3", "testpass123")

        res = self.client.patch(
            f"/api/users/users/{target.id}/enable-student/",
            {"enabled": True},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data["student_enabled"])

    def test_non_admin_cannot_enable_instructor(self):
        User.objects.create_user(username="normal1", password="testpass123")
        target = User.objects.create_user(username="normal2", password="testpass123")
        self.auth_as("normal1", "testpass123")

        res = self.client.patch(
            f"/api/users/users/{target.id}/enable-instructor/",
            {"enabled": True},
            format="json",
        )
        self.assertIn(res.status_code, (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN))

    def test_admin_flags_patch(self):
        self.make_admin(username="admin4", password="testpass123")
        target = User.objects.create_user(username="u6", password="testpass123")
        self.auth_as("admin4", "testpass123")

        res = self.client.patch(
            f"/api/users/users/{target.id}/admin-flags/",
            {"instructor_enabled": True, "is_active": False},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data["instructor_enabled"])
        self.assertFalse(res.data["is_active"])
