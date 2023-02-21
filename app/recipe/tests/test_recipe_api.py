"""
Tests for recipe api's
"""

from decimal import Decimal
from django.contrib.auth import get_user_model

import tempfile
import os
from PIL import Image

from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import (
    Recipe,
    Tag,
    Ingredient    
)
from recipe.serializers import (
    RecipeSerializer,
    RecipeDetailSerializer,
)



RECIPES_URL = reverse('recipe:recipe-list')

def detail_url(recipe_id):
    """Create and return a recipe detail url"""
    return reverse('recipe:recipe-detail', args=[recipe_id])

def image_upload_url(recipe_id):
    """Create and return a recipe detail URL"""
    return reverse('recipe:recipe-upload-image', args=[recipe_id])

def create_recipe(user, **params):
    """Create and return a sample recipe"""
    defaults = {
        'title' : 'sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description':'Sample description',
        'link': 'http://example.com/recipe.pdf'
    }
    defaults.update(params)
    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe

def create_user(**params):
    """Create and return a new user"""
    return get_user_model().objects.create_user(**params)

class PublicRecipeAPITests(TestCase):
    """Test unathenticated api requests"""
    def setUP(self):
        # get test client
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API"""
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRecipeAPITests(TestCase):
    """Test authenticated api requests"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='testpass123')
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        """Test retrieving list of recipes"""
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.all().order_by('-id')
        # many = true, to pass in list of items
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limited_to_user(self):
        """Test list of recipes is limitied to authed user"""
        other_user = create_user(email='other@example.com', password='otherpasswerod123'        )
        create_recipe(user = other_user)
        create_recipe(user = self.user)

        res = self.client.get(RECIPES_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        """Test get recipe detail"""
        recipe = create_recipe(user = self.user)
        url = detail_url(recipe.id)
        res = self.client.get(url)

        # many = true not provided because we are passing in one recipe
        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.data, serializer.data)


    def test_create_recipe(self):
        """Test creating a recipe"""
        payload = {
            'title' : 'sample recipe',
            'time_minutes': 30,
            'price': Decimal('5.99'),
            'description':'Sample description',
            'link': 'http://example.com/recipe.pdf'
        }
        res = self.client.post(RECIPES_URL, payload) # /api/recipes/recipe

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        # check that all keys match
        for k, v in payload.items():
            self.assertEqual(getattr(recipe, k), v)

        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        """Test partial update of a recipe"""
        # make sure other fields are not updated during this change 
        original_link = 'https://example.com/recipe.pdf'
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe',
            link = original_link
        )

        payload = {'title': 'new recipe title'}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # refresh the recipe with new fields added to db
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.link, original_link)
        self.assertEqual(recipe.user, self.user)


    def test_full_update(self):
        """Test full recipe update"""
        recipe = create_recipe(
            user = self.user,
            title = "sample title",
            link = 'https://example.com/recipe.pdf',
            description = 'sample description',
        )

        payload = {
            'title': 'new recipe title',
            'link': 'https://example.com/new-recipe.pdf',
            'description': 'new descr',
            'time_minutes': 10,
            'price': Decimal('2.50')
        }
        url = detail_url(recipe.id)
        res = self.client.put(url, payload)
        self.assertEqual(res.status_code , status.HTTP_200_OK)
        recipe.refresh_from_db()
        for k,v in payload.items():
            self.assertEqual(getattr(recipe,k),v)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        """test changing the recipe user results in an error"""
        new_user = create_user(email='user2@example.com', password='testpass123')
        recipe = create_recipe(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        self.client.patch(url,payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        recipe = create_recipe(user = self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        # make sure that the recipe was deleted
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_delete_other_users_recipe_error(self):
        """Test trying to delete other users recipe gives error"""
        new_user = create_user(email='user2@example.com', password='password1234')
        recipe = create_recipe(user = new_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        # check that we did not delete other user's recipe
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())

    def test_create_recipe_with_new_tags(self):
        """test creating a recipe with new tags"""
        payload ={
            'title':'Thai curry',
            'time_minutes': 30,
            'price': Decimal('3.56'),
            'tags': [{'name': 'Thai'}, {'name':'Dinner'}]
        }
        res = self.client.post(RECIPES_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(),1) #avoid index error
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(),2)
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user = self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        """Test creating recipe with existing tag"""
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        payload = {
            'title': 'Pongal',
            'time_minutes':60,
            'price': Decimal('4.60'),
            'tags': [{'name':'Indian'}, {'name':'Breakfast'}]
        }
        res = self.client.post(RECIPES_URL, payload, format="json")

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(),1)
        recipe = recipes[0]
        self.assertEqual(recipe.tags.count(),2)
        self.assertIn(tag_indian, recipe.tags.all())
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name = tag['name'],
                user = self.user
            ).exists()
            self.assertTrue(exists)
    
    def test_create_tag_on_update(self):
        """Test creating tag when updating a recipe"""
        recipe = create_recipe(user = self.user)

        payload = {'tags':[{'name': 'Lunch'}]}
        url = detail_url(recipe.id)
        # partial update request
        res = self.client.patch(url, payload, format='json')

        # dont need refresh db in many to many fields
        self.assertEqual(res.status_code,status.HTTP_200_OK)
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        """Test assigning existing tag when updating a recipe"""
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        recipe = create_recipe(user = self.user)
        recipe.tags.add(tag_breakfast)

        # ground truth
        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')

        # test endpoint (add Lunch tag to the recipe made above)
        payload = {'tags':[{'name':'Lunch'}]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
    
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # check that the added tag actually shows up in the recipe
        self.assertIn(tag_lunch, recipe.tags.all())
        # check that breakfast is not in tags because we completely overwrote the tags (in payload)
        self.assertNotIn(tag_breakfast, recipe.tags.all())


    def test_clear_recipe_tags(self):
        """Test clearing a recipe's tags"""
        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)

        # override tags with empty list
        payload = {'tags':[]}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # make sure that no more tags exist in this recipe
        self.assertEqual(recipe.tags.count(),0)

    def test_create_recipe_with_new_ingredients(self):
        """Test creating a recipe with new ingredients"""
        payload = {
            'title':'Beef tacos',
            'time_minutes':12,
            'price':Decimal('4.90'),
            'ingredients':[{'name':'beef'},{'name':'salt'}]
        }

        res = self.client.post(RECIPES_URL, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(),1)
        recipe = recipes[0]

        self.assertEqual(recipe.ingredients.count(),2)
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user = self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_recipe_with_existing_ingredient(self):
        """Test creating a new recupe with existing ingredient"""
        ingredient = Ingredient.objects.create(user=self.user, name='Lemon')
        payload = {
            'title':'Viet soup',
            'time_minutes':12,
            'price':Decimal('4.90'),
            'ingredients':[{'name':'Lemon'},{'name':'fish'}]
        }
        res = self.client.post(RECIPES_URL,payload,format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(),1)
        recipe = recipes[0]
        self.assertEqual(recipe.ingredients.count(),2)
        self.assertIn(ingredient, recipe.ingredients.all())
        for i in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name = i['name'],
                user = self.user
            ).exists()
            self.assertTrue(exists)

    def test_create_ingredient_on_update(self):
        """Test creating an ingredient when updating a recipe"""
        recipe = create_recipe(user=self.user)

        payload = {
            'ingredients': [{'name':'potatoes'}]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url,payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_ingredient = Ingredient.objects.get(user = self.user, name='potatoes')
        self.assertIn(new_ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        """Test assigning an existing ingredient when updating a recipe"""
        recipe = create_recipe(user = self.user)
        ingredient1 = Ingredient.objects.create(user=self.user,name='Graps')
        recipe.ingredients.add(ingredient1)

        ingredient2 = Ingredient.objects.create(user=self.user,name='Apples')
        payload = {
            'ingredients':[{'name':'Apples'}]
        }

        url = detail_url(recipe.id)
        res = self.client.patch(url,payload,format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingredient2, recipe.ingredients.all())
        self.assertNotIn(ingredient1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        recipe = create_recipe(user=self.user)
        ingredient = Ingredient.objects.create(user=self.user, name='garbage')
        recipe.ingredients.add(ingredient)

        payload = {
            'ingredients':[]
        }
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(),0)

    def test_filter_by_tags(self):
        """Test filtering recipes by tags"""
        r1 = create_recipe(user = self.user, title='thai curry')
        r2 = create_recipe(user = self.user, title='eggyplant')

        tag1 = Tag.objects.create(user=self.user, name='vegan')
        tag2 = Tag.objects.create(user=self.user, name='vegetarian')
        r1.tags.add(tag1)
        r2.tags.add(tag2)

        r3 = create_recipe(user = self.user, title='fish and chips')
        params = {'tags': f'{tag1.id},{tag2.id}'}
        res = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        # tag was not specified for s3
        self.assertNotIn(s3.data, res.data)


    def test_filter_by_ingredients(self):
        """Test filtering recipes by ingredients"""
        r1 = create_recipe(user = self.user, title='beans on toast')
        r2 = create_recipe(user = self.user, title='chicken nuggies')

        ing1 = Ingredient.objects.create(user=self.user, name='beans')
        ing2 = Ingredient.objects.create(user=self.user, name='chicken')
        r1.ingredients.add(ing1)
        r2.ingredients.add(ing2)

        r3 = create_recipe(user = self.user, title='fish and chips')
        # ingredients to filter by
        params = {'ingredients': f'{ing1.id},{ing2.id}'}
        res = self.client.get(RECIPES_URL, params)

        s1 = RecipeSerializer(r1)
        s2 = RecipeSerializer(r2)
        s3 = RecipeSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        # tag was not specified for s3
        self.assertNotIn(s3.data, res.data)



class ImageUploadTests(TestCase):
    """Tests for the image upload API"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
        self.recipe = create_recipe(user = self.user)

    def tearDown(self):
        # we dont want to be building up test images on our machine
        self.recipe.image.delete()

    def test_upload_image(self):
        """Test uploading an image to a recipe."""
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            img = Image.new('RGB',(10,10))
            # save image to temp file
            img.save(image_file, format='JPEG')
            # move pointer to start of file (because save moves it to the end)
            image_file.seek(0)
            payload = {'image': image_file}
            res = self.client.post(url, payload, format='multipart')
        
        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image',res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        """Test uploading invalid iamge"""
        url = image_upload_url(self.recipe.id)
        payload = {'image':'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)






