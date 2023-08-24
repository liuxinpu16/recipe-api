from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (Ingredient, Recipe)
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

    def test_filter_ingredients_assigned_to_recipe(self):
        in1 = Ingredient.objects.create(user=self.user, name='in1')
        in2 = Ingredient.objects.create(user=self.user, name='in2')
        recipe = Recipe.objects.create(
            title='Recipe1',
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user
        )
        recipe.ingredients.add(in1)
        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        s1 = IngredientSerializer(in1)
        s2 = IngredientSerializer(in2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_ingredients_unique(self):
        in1 = Ingredient.objects.create(user=self.user, name='in1')
        Ingredient.objects.create(user=self.user, name='in2')
        recipe1 = Recipe.objects.create(
            title='Recipe1',
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user
        )
        recipe2 = Recipe.objects.create(
            title='Recipe2',
            time_minutes=5,
            price=Decimal('4.50'),
            user=self.user
        )
        recipe1.ingredients.add(in1)
        recipe2.ingredients.add(in1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})
        self.assertEqual(len(res.data), 1)
