import unittest
from sql_mongo_converter import sql_to_mongo, mongo_to_sql


class TestConverter(unittest.TestCase):
    """
    Unit tests for the SQL to MongoDB and MongoDB to SQL conversion functions.
    """

    def test_sql_to_mongo_basic(self):
        """
        Test basic SQL to MongoDB conversion.

        :return: None
        """
        sql = "SELECT name, age FROM users WHERE age > 30 AND name = 'Alice';"
        result = sql_to_mongo(sql)
        expected_filter = {
            "age": {"$gt": 30},
            "name": "Alice"
        }
        self.assertEqual(result["collection"], "users")
        self.assertEqual(result["find"], expected_filter)
        self.assertEqual(result["projection"], {"name": 1, "age": 1})

    def test_mongo_to_sql_basic(self):
        """
        Test basic MongoDB to SQL conversion.

        :return: None
        """
        mongo_obj = {
            "collection": "users",
            "find": {
                "age": {"$gte": 25},
                "status": "ACTIVE"
            },
            "projection": {"age": 1, "status": 1}
        }
        sql = mongo_to_sql(mongo_obj)
        # e.g. SELECT age, status FROM users WHERE age >= 25 AND status = 'ACTIVE';
        self.assertIn("SELECT age, status FROM users WHERE age >= 25 AND status = 'ACTIVE';", sql)


if __name__ == "__main__":
    unittest.main()

# Should output:
# Testing started at 18:02 ...
# Launching unittests with arguments python -m unittest /Users/davidnguyen/PycharmProjects/SQL-Mongo-Queries-Converter/tests/test_converter.py in /Users/davidnguyen/PycharmProjects/SQL-Mongo-Queries-Converter/tests
#
#
# Ran 2 tests in 0.004s
#
# OK
#
# Process finished with exit code 0
