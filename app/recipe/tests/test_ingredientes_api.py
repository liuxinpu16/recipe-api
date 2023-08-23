from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientSerializer


INGREDIENTS_URL = reverse('recipe:ingredient-list')


def detail_url(igredient_id):
    return reverse('recipe:ingredient-detail', args=[igredient_id])


def create_user(email='test@example.com', password='password'):
    return get_user_model().objects.create_user(email, password)


class PublicIngredientApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredients(self):
        Ingredient.objects.create(user=self.user, name='Kale')
        Ingredient.objects.create(user=self.user, name='Potato')

        res = self.client.get(INGREDIENTS_URL)
        ingreients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingreients, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limited_to_user(self):
        other_user = create_user(
            email='other@example.com', password='testpass123')
        Ingredient.objects.create(user=other_user, name='Potato')
        ingriedient = Ingredient.objects.create(user=self.user, name='Kale')

        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingriedient.name)
        self.assertEqual(res.data[0]['id'], ingriedient.id)

    def test_update_ingredient(self):
        ingriedient = Ingredient.objects.create(user=self.user, name='Kale')
        payload = {
            'name': 'Potato',
        }
        url = detail_url(ingriedient.id)
        res = self.client.patch(url, payload)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingriedient.refresh_from_db()
        self.assertEqual(ingriedient.name, payload['name'])

    def test_delete_ingredient(self):
        ingriedient = Ingredient.objects.create(user=self.user, name='Kale')
        url = detail_url(ingriedient.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        ingriedients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingriedients.exists())
