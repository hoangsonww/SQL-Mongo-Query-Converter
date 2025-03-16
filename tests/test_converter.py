import unittest
from sql_mongo_converter import sql_to_mongo, mongo_to_sql

class TestConverter(unittest.TestCase):
    def test_sql_to_mongo_basic(self):
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
