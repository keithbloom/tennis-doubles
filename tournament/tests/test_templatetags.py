from django.test import TestCase
from django.template import Context, Template

class CustomTagsTest(TestCase):
    def test_get_item_filter_with_list(self):
        """Test get_item filter with a list"""
        template = Template('{% load custom_tags %}{{ mylist|get_item:1 }}')
        context = Context({'mylist': ['a', 'b', 'c']})
        output = template.render(context)
        self.assertEqual(output.strip(), 'b')

    def test_get_item_filter_with_dict(self):
        """Test get_item filter with a dictionary"""
        template = Template('{% load custom_tags %}{{ mydict|get_item:"key" }}')
        context = Context({'mydict': {'key': 'value'}})
        output = template.render(context)
        self.assertEqual(output.strip(), 'value')

    def test_get_item_filter_out_of_bounds(self):
        """Test get_item filter with out of bounds index"""
        template = Template('{% load custom_tags %}{{ mylist|get_item:10 }}')
        context = Context({'mylist': ['a', 'b', 'c']})
        output = template.render(context)
        self.assertEqual(output.strip(), 'None')

    def test_sub_filter(self):
        """Test sub filter"""
        template = Template('{% load custom_tags %}{{ 10|sub:3 }}')
        context = Context({})
        output = template.render(context)
        self.assertEqual(output.strip(), '7')